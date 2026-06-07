"use client";

import { isAxiosError } from "axios";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "@contexts/auth";

import { getApiErrorMessage } from "@utils/common";
import { readSession, saveSession } from "@lib/auth-session";
import {
  type ProfileFieldKey,
  type ProfileFormValues,
  validatePasswordChange,
  validateProfileForm,
} from "@utils/account/validation";
import {
  accountService,
  buildProfileUpdateBody,
  mapProfileResponseToForm,
} from "@services/account";
import { brand } from "@config/brand";

import { AccountSidebar } from "./sidebar";
import { AccountPasswordSection } from "./sections/password";
import { AccountPersonalInfoSection } from "./sections/personal-info";

const emptyProfile = (): ProfileFormValues => ({
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  address: "",
  city: "",
  state: "",
  zipCode: "",
  country: "",
});

export const AccountPage = () => {
  const router = useRouter();
  const { session, ready, refresh } = useAuth();

  const [savedProfile, setSavedProfile] = useState<ProfileFormValues>(emptyProfile);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileLoadError, setProfileLoadError] = useState<string | null>(null);

  const [editingProfile, setEditingProfile] = useState(false);
  const [draftProfile, setDraftProfile] = useState<ProfileFormValues>(emptyProfile);
  const [profileErrors, setProfileErrors] = useState<Partial<Record<ProfileFieldKey, string>>>({});
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileNotice, setProfileNotice] = useState<string | null>(null);
  const [profileNoticeVariant, setProfileNoticeVariant] = useState<"error" | "success">("error");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordErrors, setPasswordErrors] = useState<Partial<Record<string, string>>>({});
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  useEffect(() => {
    if (!ready || session) return;
    router.replace("/sign-in");
  }, [ready, session, router]);

  useEffect(() => {
    if (!ready || !session) {
      return;
    }

    const ac = new AbortController();
    setProfileLoading(true);
    setProfileLoadError(null);

    (async () => {
      try {
        const data = await accountService.getProfile({ signal: ac.signal });
        if (ac.signal.aborted) return;
        const next = mapProfileResponseToForm(data);
        setSavedProfile(next);
        setDraftProfile(next);
        setAvatarUrl(data.avatar_url ?? null);
      } catch (e) {
        if (ac.signal.aborted) return;
        setProfileLoadError(getApiErrorMessage(e));
      } finally {
        if (!ac.signal.aborted) {
          setProfileLoading(false);
        }
      }
    })();

    return () => ac.abort();
  }, [ready, session]);

  const emailFromSession = session?.user.email?.trim() ?? "";

  const mergedSavedProfile = useMemo(
    () => ({
      ...savedProfile,
      email: savedProfile.email.trim() || emailFromSession,
    }),
    [savedProfile, emailFromSession],
  );

  const startEditProfile = useCallback(() => {
    setDraftProfile({ ...mergedSavedProfile });
    setProfileErrors({});
    setProfileNotice(null);
    setEditingProfile(true);
  }, [mergedSavedProfile]);

  const cancelEditProfile = useCallback(() => {
    setEditingProfile(false);
    setProfileErrors({});
    setProfileNotice(null);
  }, []);

  const uploadAvatar = useCallback(async (file: File) => {
    setAvatarUploading(true);
    setProfileNotice(null);
    try {
      const data = await accountService.uploadAvatar(file);
      setAvatarUrl(data.avatar_url ?? null);
      setProfileNoticeVariant("success");
      setProfileNotice("Photo updated.");
    } catch (e) {
      setProfileNoticeVariant("error");
      setProfileNotice(getApiErrorMessage(e));
    } finally {
      setAvatarUploading(false);
    }
  }, []);

  const persistSessionEmailIfNeeded = useCallback(
    (email: string | null) => {
      if (!session || !email?.trim()) return;
      const trimmed = email.trim();
      if (trimmed === (session.user.email ?? "").trim()) return;
      const stored = readSession();
      if (!stored) return;
      saveSession({
        ...stored,
        user: { ...stored.user, email: trimmed },
      });
      refresh();
    },
    [session, refresh],
  );

  const saveProfile = useCallback(async () => {
    const next = { ...draftProfile };
    const errors = validateProfileForm(next);
    if (Object.keys(errors).length > 0) {
      setProfileErrors(errors);
      return;
    }

    const patch = buildProfileUpdateBody(next, mergedSavedProfile);
    if (Object.keys(patch).length === 0) {
      setProfileNoticeVariant("error");
      setProfileNotice("No changes to save.");
      return;
    }

    setProfileErrors({});
    setProfileNotice(null);
    setProfileSaving(true);
    try {
      const data = await accountService.updateProfile(patch);
      const updated = mapProfileResponseToForm(data);
      setSavedProfile(updated);
      setDraftProfile(updated);
      persistSessionEmailIfNeeded(data.email);
      setEditingProfile(false);
      setProfileNoticeVariant("success");
      setProfileNotice("Profile saved.");
    } catch (e) {
      if (isAxiosError(e) && e.response?.status === 409) {
        setProfileNotice(null);
        setProfileErrors((prev) => ({ ...prev, email: getApiErrorMessage(e) }));
      } else {
        setProfileNoticeVariant("error");
        setProfileNotice(getApiErrorMessage(e));
      }
    } finally {
      setProfileSaving(false);
    }
  }, [draftProfile, mergedSavedProfile, persistSessionEmailIfNeeded]);

  const updateDraft = useCallback((key: ProfileFieldKey, value: string) => {
    setDraftProfile((p) => ({ ...p, [key]: value }));
    setProfileErrors((e) => {
      if (!e[key]) return e;
      const next = { ...e };
      delete next[key];
      return next;
    });
  }, []);

  const submitPasswordChange = useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      setPasswordSuccess(false);
      const values = { currentPassword, newPassword, confirmPassword };
      const errors = validatePasswordChange(values);
      if (Object.keys(errors).length > 0) {
        setPasswordErrors(errors);
        return;
      }
      setPasswordErrors({});
      setPasswordSubmitting(true);
      try {
        await accountService.changePassword({
          current_password: currentPassword,
          new_password: newPassword,
        });
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setPasswordSuccess(true);
      } catch (err) {
        const msg = getApiErrorMessage(err);
        if (isAxiosError(err) && err.response?.status === 401) {
          setPasswordErrors({ currentPassword: msg });
        } else {
          setPasswordErrors({ form: msg });
        }
      } finally {
        setPasswordSubmitting(false);
      }
    },
    [currentPassword, newPassword, confirmPassword],
  );

  const onChangeCurrentPassword = useCallback((v: string) => {
    setCurrentPassword(v);
    setPasswordErrors((e) => {
      if (!e.currentPassword) return e;
      const next = { ...e };
      delete next.currentPassword;
      delete next.form;
      return next;
    });
    setPasswordSuccess(false);
  }, []);

  const onChangeNewPassword = useCallback((v: string) => {
    setNewPassword(v);
    setPasswordErrors((e) => {
      const next = { ...e };
      delete next.newPassword;
      delete next.confirmPassword;
      delete next.form;
      return next;
    });
    setPasswordSuccess(false);
  }, []);

  const onChangeConfirmPassword = useCallback((v: string) => {
    setConfirmPassword(v);
    setPasswordErrors((e) => {
      if (!e.confirmPassword) return e;
      const next = { ...e };
      delete next.confirmPassword;
      delete next.form;
      return next;
    });
    setPasswordSuccess(false);
  }, []);

  if (!ready || !session) {
    return null;
  }

  if (profileLoadError) {
    return (
      <main className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
        <p className="text-sm text-destructive" role="alert">
          {profileLoadError}
        </p>
      </main>
    );
  }

  const profileValues = editingProfile ? draftProfile : mergedSavedProfile;

  return (
    <div className="flex flex-col lg:flex-row">
      <AccountSidebar />

      <main className="min-w-0 flex-1 px-4 py-10 sm:px-6 lg:px-10">
        <div className="mx-auto w-full max-w-3xl">
          <header className="border-b border-border pb-8">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              {brand.account.workspaceLabel}
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
              {brand.account.title}
            </h1>
            <p className="mt-2 max-w-xl text-sm text-muted-foreground">{brand.account.subtitle}</p>
          </header>

          <div className="mt-10 flex flex-col gap-10">
            <div id="profile" className="scroll-mt-24">
              <AccountPersonalInfoSection
                editing={editingProfile}
                values={profileValues}
                errors={profileErrors}
                notice={profileNotice}
                noticeVariant={profileNoticeVariant}
                saving={profileSaving}
                profileLoading={profileLoading}
                avatarUrl={avatarUrl}
                avatarUploading={avatarUploading}
                onUploadAvatar={uploadAvatar}
                onEdit={startEditProfile}
                onCancel={cancelEditProfile}
                onSave={saveProfile}
                onChangeField={updateDraft}
              />
            </div>

            <div id="security" className="scroll-mt-24">
              <AccountPasswordSection
                currentPassword={currentPassword}
                newPassword={newPassword}
                confirmPassword={confirmPassword}
                errors={passwordErrors}
                submitting={passwordSubmitting}
                success={passwordSuccess}
                onChangeCurrent={onChangeCurrentPassword}
                onChangeNew={onChangeNewPassword}
                onChangeConfirm={onChangeConfirmPassword}
                onSubmit={submitPasswordChange}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
