"use client";

import { Button } from "@components/ui/buttons";
import { Avatar } from "@components/ui/voyager/avatar";
import { SaveCancelGroup } from "@components/ui/save-cancel-group";

import type { ProfileFieldKey, ProfileFormValues } from "@utils/account/validation";

import { AccountField } from "../field";
import { ACCOUNT_SECTION_CARD_CLASS } from "../styles";

export type AccountPersonalInfoSectionProps = {
  editing: boolean;
  values: ProfileFormValues;
  errors: Partial<Record<ProfileFieldKey, string>>;
  notice?: string | null;
  noticeVariant?: "error" | "success";
  saving?: boolean;
  profileLoading?: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSave: () => void;
  onChangeField: (key: ProfileFieldKey, value: string) => void;
};

export const AccountPersonalInfoSection = ({
  editing,
  values,
  errors,
  notice = null,
  noticeVariant = "error",
  saving = false,
  profileLoading = false,
  onEdit,
  onCancel,
  onSave,
  onChangeField,
}: AccountPersonalInfoSectionProps) => {
  const displayName =
    `${values.firstName} ${values.lastName}`.trim() || values.email.trim() || "User";
  const locationLine =
    [values.city, values.state].filter((v) => v.trim()).join(", ") ||
    values.country.trim();

  return (
  <section
    className={ACCOUNT_SECTION_CARD_CLASS}
    aria-labelledby="personal-heading"
    aria-busy={profileLoading}
  >
    {notice ? (
      <p
        className={
          noticeVariant === "error"
            ? "mb-4 text-sm text-destructive"
            : "mb-4 text-sm font-medium text-emerald-600 dark:text-emerald-500"
        }
        role={noticeVariant === "error" ? "alert" : "status"}
      >
        {notice}
      </p>
    ) : null}
    <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 id="personal-heading" className="text-lg font-semibold text-foreground">
          Personal information
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">Your name, contact details, and address.</p>
      </div>
      <div className="flex shrink-0 flex-wrap gap-2 sm:justify-end">
        {!editing ? (
          <Button
            type="button"
            variant="outline"
            size="default"
            onClick={onEdit}
            disabled={profileLoading}
          >
            Edit
          </Button>
        ) : (
          <SaveCancelGroup onCancel={onCancel} onSave={onSave} saving={saving} />
        )}
      </div>
    </div>

    <div className="mt-6 flex flex-col gap-10 lg:flex-row">
      <div className="flex flex-shrink-0 flex-col items-center lg:items-start">
        <Avatar
          sizeClass="w-28 h-28 sm:w-32 sm:h-32"
          radius="rounded-2xl"
          userName={displayName}
          containerClassName="ring-1 ring-neutral-200 dark:ring-neutral-700"
        />
        {locationLine ? (
          <p className="mt-3 text-center text-sm text-neutral-500 lg:text-left dark:text-neutral-400">
            {locationLine}
          </p>
        ) : null}
      </div>

      <div className="grid min-w-0 flex-grow grid-cols-1 gap-5 sm:grid-cols-2">
      <AccountField
        id="account-firstName"
        label="First name"
        value={values.firstName}
        onChange={(v) => onChangeField("firstName", v)}
        error={editing ? errors.firstName : null}
        readOnly={!editing}
      />
      <AccountField
        id="account-lastName"
        label="Last name"
        value={values.lastName}
        onChange={(v) => onChangeField("lastName", v)}
        error={editing ? errors.lastName : null}
        readOnly={!editing}
      />
      <AccountField
        id="account-email"
        label="Email"
        type="email"
        autoComplete="email"
        value={values.email}
        onChange={(v) => onChangeField("email", v)}
        error={editing ? errors.email : null}
        readOnly={!editing}
      />
      <AccountField
        id="account-phone"
        label="Phone"
        type="tel"
        autoComplete="tel"
        value={values.phone}
        onChange={(v) => onChangeField("phone", v)}
        error={editing ? errors.phone : null}
        readOnly={!editing}
      />
      <AccountField
        id="account-address"
        label="Street address"
        autoComplete="street-address"
        value={values.address}
        onChange={(v) => onChangeField("address", v)}
        error={editing ? errors.address : null}
        readOnly={!editing}
        className="sm:col-span-2"
      />
      <AccountField
        id="account-city"
        label="City"
        autoComplete="address-level2"
        value={values.city}
        onChange={(v) => onChangeField("city", v)}
        error={editing ? errors.city : null}
        readOnly={!editing}
      />
      <AccountField
        id="account-state"
        label="State / province"
        autoComplete="address-level1"
        value={values.state}
        onChange={(v) => onChangeField("state", v)}
        error={editing ? errors.state : null}
        readOnly={!editing}
      />
      <AccountField
        id="account-zipCode"
        label="ZIP / postal code"
        autoComplete="postal-code"
        value={values.zipCode}
        onChange={(v) => onChangeField("zipCode", v)}
        error={editing ? errors.zipCode : null}
        readOnly={!editing}
      />
      <AccountField
        id="account-country"
        label="Country"
        autoComplete="country-name"
        value={values.country}
        onChange={(v) => onChangeField("country", v)}
        error={editing ? errors.country : null}
        readOnly={!editing}
      />
      </div>
    </div>
  </section>
  );
};
