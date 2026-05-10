"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "@contexts/auth";

import {
  type ProfileFieldKey,
  type ProfileFormValues,
  validatePasswordChange,
  validateProfileForm,
} from "@lib/account-validation";

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

const AccountPageSkeleton = () => (
  <main className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
    <div className="h-9 w-48 animate-pulse rounded-md bg-muted" />
    <div className="mt-2 h-4 w-72 max-w-full animate-pulse rounded-md bg-muted" />
    <div className="mt-10 h-64 animate-pulse rounded-xl bg-muted/60" />
    <div className="mt-8 h-72 animate-pulse rounded-xl bg-muted/60" />
  </main>
);

export const AccountPage = () => {
  const router = useRouter();
  const { session, ready } = useAuth();

  const [savedProfile, setSavedProfile] = useState<ProfileFormValues>(emptyProfile);
  const [editingProfile, setEditingProfile] = useState(false);
  const [draftProfile, setDraftProfile] = useState<ProfileFormValues>(emptyProfile);
  const [profileErrors, setProfileErrors] = useState<Partial<Record<ProfileFieldKey, string>>>({});

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
    setEditingProfile(true);
  }, [mergedSavedProfile]);

  const cancelEditProfile = useCallback(() => {
    setEditingProfile(false);
    setProfileErrors({});
  }, []);

  const saveProfile = useCallback(() => {
    const next = { ...draftProfile };
    const errors = validateProfileForm(next);
    if (Object.keys(errors).length > 0) {
      setProfileErrors(errors);
      return;
    }
    setSavedProfile(next);
    setEditingProfile(false);
    setProfileErrors({});
  }, [draftProfile]);

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
      await new Promise((r) => setTimeout(r, 400));
      setPasswordSubmitting(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordSuccess(true);
    },
    [currentPassword, newPassword, confirmPassword],
  );

  const onChangeCurrentPassword = useCallback((v: string) => {
    setCurrentPassword(v);
    setPasswordErrors((e) => {
      if (!e.currentPassword) return e;
      const next = { ...e };
      delete next.currentPassword;
      return next;
    });
  }, []);

  const onChangeNewPassword = useCallback((v: string) => {
    setNewPassword(v);
    setPasswordErrors((e) => {
      const next = { ...e };
      delete next.newPassword;
      delete next.confirmPassword;
      return next;
    });
  }, []);

  const onChangeConfirmPassword = useCallback((v: string) => {
    setConfirmPassword(v);
    setPasswordErrors((e) => {
      if (!e.confirmPassword) return e;
      const next = { ...e };
      delete next.confirmPassword;
      return next;
    });
  }, []);

  if (!ready) {
    return <AccountPageSkeleton />;
  }

  if (!session) {
    return null;
  }

  const profileValues = editingProfile ? draftProfile : mergedSavedProfile;

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
      <header className="border-b border-border pb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">Account</h1>
        <p className="mt-2 max-w-xl text-sm text-muted-foreground">Manage your profile and security.</p>
      </header>

      <div className="mt-10 flex flex-col gap-10">
        <AccountPersonalInfoSection
          editing={editingProfile}
          values={profileValues}
          errors={profileErrors}
          onEdit={startEditProfile}
          onCancel={cancelEditProfile}
          onSave={saveProfile}
          onChangeField={updateDraft}
        />

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
    </main>
  );
};
