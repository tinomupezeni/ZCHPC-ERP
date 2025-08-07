import React, { ReactNode, useEffect } from "react";

interface ModalProps {
  isOpen: boolean;                   // Controls modal visibility
  onClose: () => void;               // Handler to close the modal
  title?: string;                   // Optional modal title
  children: ReactNode;              // Modal content/body
  footer?: ReactNode;               // Optional footer (buttons, actions)
  closeOnOutsideClick?: boolean;   // Whether clicking outside closes modal (default true)
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  closeOnOutsideClick = true,
}: ModalProps) {
  // Close on ESC key press
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }
    if (isOpen) {
      window.addEventListener("keydown", onKeyDown);
    }
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  // Prevent scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  // Handle outside click to close
  const onBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnOutsideClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={onBackdropClick}
      aria-modal="true"
      role="dialog"
      aria-labelledby={title ? "modal-title" : undefined}
      tabIndex={-1}
    >
      <div
        className="bg-white rounded-lg shadow-lg max-w-lg w-full mx-4 p-6 relative"
        role="document"
      >
        {title && (
          <h2 id="modal-title" className="text-xl font-semibold mb-4">
            {title}
          </h2>
        )}

        <div className="mb-6">{children}</div>

        {footer && <div className="flex justify-end space-x-3">{footer}</div>}

        {/* Close button top-right */}
        <button
          onClick={onClose}
          aria-label="Close modal"
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-700"
          type="button"
        >
          &#x2715;
        </button>
      </div>
    </div>
  );
}
