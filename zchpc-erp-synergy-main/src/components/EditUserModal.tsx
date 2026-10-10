import React, { useEffect, useState } from "react";
import { Input } from "./ui/input";
import { toast } from "sonner";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { getUser, updateUser } from "@/services/auth.services";
import { NO_PERMISSION, readApiError } from "@/lib/apiErrors";

/**
 * Edit a login's name (B8). PATCH /auth/users/{id}/ accepts first_name and
 * last_name (and is_active, which the Users list handles); role, department
 * and pay live on the employee record in HR, not here.
 */
const EditUserModal = ({ closeModal, userId, onSaved }) => {
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;
    getUser(userId)
      .then(({ data }) => {
        if (cancelled) return;
        setEmail(data.email ?? "");
        setFirstName(data.first_name ?? "");
        setLastName(data.last_name ?? "");
        setLoaded(true);
      })
      .catch((error) => {
        if (cancelled) return;
        const { status } = readApiError(error);
        toast.error(status === 403 ? NO_PERMISSION : "We couldn't load this user.");
        closeModal();
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    setFieldErrors({});
    try {
      await updateUser(userId, { first_name: firstName.trim(), last_name: lastName.trim() });
      toast.success("User updated.");
      onSaved?.();
      closeModal();
    } catch (error) {
      const { status, fieldErrors: errors } = readApiError(error);
      if (status === 400 && Object.keys(errors).length > 0) {
        setFieldErrors(errors);
      } else if (status === 403) {
        toast.error(NO_PERMISSION);
      } else if (status === 404) {
        toast.error("This user no longer exists.");
        onSaved?.();
        closeModal();
      } else {
        toast.error("We couldn't save the changes. Please try again.");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center w-full">
      <form
        onSubmit={handleSubmit}
        className="p-6 bg-white rounded-lg space-y-4 w-full max-w-lg shadow-lg"
      >
        <div className="pb-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Edit user</h2>
          <button
            type="button"
            onClick={closeModal}
            aria-label="Close"
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        {!loaded ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : (
          <>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={email} disabled className="mt-1" />
            </div>
            <div>
              <Label htmlFor="first_name">First name</Label>
              <Input
                id="first_name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
                maxLength={150}
                className="mt-1"
              />
              {fieldErrors.first_name && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.first_name}</p>
              )}
            </div>
            <div>
              <Label htmlFor="last_name">Last name</Label>
              <Input
                id="last_name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
                maxLength={150}
                className="mt-1"
              />
              {fieldErrors.last_name && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.last_name}</p>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Role, department and pay are changed on the employee record in HR.
            </p>
          </>
        )}

        <div className="flex justify-end space-x-4 pt-2">
          <Button type="button" onClick={closeModal} variant="outline">
            Cancel
          </Button>
          <Button type="submit" disabled={!loaded || saving}>
            {saving ? "Saving..." : "Save changes"}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default EditUserModal;
