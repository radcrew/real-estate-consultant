"""Copy Supabase Auth users into the Cognito user pool and map them.

Run from ``backend/``, in this order::

    python scripts/migrate_supabase_users.py build-csv --out d:\\template.csv
    # ...run the Cognito import job on that CSV (aws cognito-idp CLI)...
    python scripts/migrate_supabase_users.py link-google
    python scripts/migrate_supabase_users.py sync-mapping --report mapping_report.csv

``build-csv`` and ``sync-mapping`` take ``--email`` (repeatable) to limit a dry run to a
few accounts. ``link-google`` and ``sync-mapping`` call Cognito admin APIs, so they need
AWS credentials with cognito-idp admin rights in the standard boto3 chain.

The CSV holds password hashes. Never commit it, and delete it once the import succeeds.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import re
from collections import Counter

import boto3
from sqlalchemy import bindparam, text

from app.core import database
from app.core.config import settings

# What `aws cognito-idp get-csv-header` returns for this pool. Every column must be present.
CSV_HEADER = (
    "profile,address,birthdate,gender,preferred_username,updated_at,website,picture,"
    "email_verified,phone_number_verified,phone_number,zoneinfo,locale,email,given_name,"
    "family_name,middle_name,name,nickname,cognito:mfa_enabled,cognito:username,password_hash"
).split(",")
# Cognito imports bcrypt with a cost factor of at most 12. Supabase uses $2a$10$.
BCRYPT = re.compile(r"^\$2[abxy]\$(\d\d)\$[./A-Za-z0-9]{53}$")
GOOGLE_PROVIDER = "Google"  # the pool's ProviderName for Google

PASSWORD_USERS_SQL = """
select id, lower(email), email_confirmed_at is not null, encrypted_password
from auth.users
where deleted_at is null and email is not null
  and not is_sso_user and not is_anonymous
  and (banned_until is null or banned_until <= now())
  and coalesce(encrypted_password, '') <> ''
"""
GOOGLE_USERS_SQL = """
select lower(u.email), i.provider_id, coalesce(u.encrypted_password, '') <> ''
from auth.identities i join auth.users u on u.id = i.user_id
where i.provider = 'google' and u.deleted_at is null and u.email is not null
"""
EMAIL_TO_ID_SQL = """
select lower(email), id from auth.users where deleted_at is null and email is not null
"""


async def fetch(sql: str, emails: list[str] | None = None) -> list:
    if emails:
        sql += " and lower(email) in :emails"
    stmt = text(sql)
    params = {}
    if emails:
        stmt = stmt.bindparams(bindparam("emails", expanding=True))
        params["emails"] = [e.lower() for e in emails]
    await database.init_db()
    try:
        async with database.DB_ASYNC_ENGINE.connect() as conn:
            return list((await conn.execute(stmt, params)).all())
    finally:
        await database.close_db()


def cognito():
    return boto3.client("cognito-idp", region_name=settings.cognito_region)


def build_csv(out: str, emails: list[str] | None) -> None:
    users = asyncio.run(fetch(PASSWORD_USERS_SQL, emails))
    rejected = []
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        for user_id, email, verified, password_hash in users:
            match = BCRYPT.match(password_hash)
            if not match or int(match.group(1)) > 12:
                rejected.append(str(user_id))  # the id only, never the hash
                continue
            row = dict.fromkeys(CSV_HEADER, "")
            row.update(
                {
                    "cognito:username": email,
                    "email": email,
                    "email_verified": "TRUE" if verified else "FALSE",
                    "phone_number_verified": "FALSE",
                    "cognito:mfa_enabled": "FALSE",
                    "password_hash": password_hash,
                }
            )
            writer.writerow(row)
    print(
        f"Wrote {len(users) - len(rejected)} user(s) to {out}. Rejected {len(rejected)}: {rejected}"
    )


def native_username(client, email: str) -> str | None:
    users = client.list_users(
        UserPoolId=settings.cognito_user_pool_id, Filter=f'email = "{email}"'
    )["Users"]
    native = [u["Username"] for u in users if not u["Username"].startswith("google_")]
    return native[0] if len(native) == 1 else None


def link_google() -> None:
    """Point each Supabase Google identity at a native Cognito user.

    Must run before that person's first Google sign-in through Cognito; afterwards the
    federated user already exists and the link is refused.
    """
    client = cognito()
    pool = settings.cognito_user_pool_id
    for email, google_sub, has_password in asyncio.run(fetch(GOOGLE_USERS_SQL)):
        username = native_username(client, email)
        if username is None and not has_password:
            client.admin_create_user(
                UserPoolId=pool,
                Username=email,
                MessageAction="SUPPRESS",
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"},
                ],
            )
            username = native_username(client, email)
        if username is None:
            print(f"EXCEPTION no native user: {email}")
            continue
        try:
            client.admin_link_provider_for_user(
                UserPoolId=pool,
                DestinationUser={"ProviderName": "Cognito", "ProviderAttributeValue": username},
                SourceUser={
                    "ProviderName": GOOGLE_PROVIDER,
                    "ProviderAttributeName": "Cognito_Subject",
                    "ProviderAttributeValue": google_sub,
                },
            )
            print(f"Linked {email}")
        except client.exceptions.ClientError as exc:
            print(f"EXCEPTION {email}: {exc.response['Error']['Message']}")


def cognito_users(client):
    kwargs = {"UserPoolId": settings.cognito_user_pool_id}
    while True:
        page = client.list_users(**kwargs)
        for user in page["Users"]:
            attrs = {a["Name"]: a["Value"] for a in user["Attributes"]}
            yield user["Username"], attrs["sub"], attrs.get("email", "").lower()
        if "PaginationToken" not in page:
            return
        kwargs["PaginationToken"] = page["PaginationToken"]


async def insert_mappings(pairs: list[dict]) -> None:
    if not pairs:
        return
    await database.init_db()
    try:
        async with database.DB_ASYNC_ENGINE.begin() as conn:
            await conn.execute(
                text(
                    "insert into public.cognito_identity_mapping (sub, uuid) "
                    "values (:sub, :uuid) on conflict do nothing"
                ),
                pairs,
            )
    finally:
        await database.close_db()


def sync_mapping(report_path: str, emails: list[str] | None) -> None:
    supabase_ids = dict(asyncio.run(fetch(EMAIL_TO_ID_SQL, emails)))
    wanted = {e.lower() for e in emails} if emails else None
    report, pairs = [], []
    for username, sub, email in cognito_users(cognito()):
        if wanted is not None and email not in wanted:
            continue
        user_id = supabase_ids.get(email)
        if username.startswith("google_"):
            status = "EXCEPTION_FEDERATED"
        elif user_id is None:
            status = "NO_SUPABASE_USER"
        else:
            status = "MATCHED"
            pairs.append({"sub": sub, "uuid": user_id})
        report.append(
            {
                "email": email,
                "cognito_sub": sub,
                "supabase_uuid": str(user_id or ""),
                "status": status,
            }
        )

    asyncio.run(insert_mappings(pairs))
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "cognito_sub", "supabase_uuid", "status"])
        writer.writeheader()
        writer.writerows(report)
    print(dict(Counter(r["status"] for r in report)), f"report: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    steps = parser.add_subparsers(dest="step", required=True)
    p = steps.add_parser("build-csv", help="Write the Cognito import CSV.")
    p.add_argument("--out", required=True)
    p.add_argument("--email", action="append", help="Limit to these emails (dry run).")
    steps.add_parser("link-google", help="Link Supabase Google identities to Cognito users.")
    p = steps.add_parser("sync-mapping", help="Fill public.cognito_identity_mapping.")
    p.add_argument("--report", default="mapping_report.csv")
    p.add_argument("--email", action="append", help="Limit to these emails (dry run).")
    args = parser.parse_args()

    if args.step == "build-csv":
        build_csv(args.out, args.email)
    elif args.step == "link-google":
        link_google()
    else:
        sync_mapping(args.report, args.email)


if __name__ == "__main__":
    main()
