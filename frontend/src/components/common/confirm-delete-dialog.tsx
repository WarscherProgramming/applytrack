import { Loader2 } from 'lucide-react';
import type { ReactNode } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface ConfirmDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  title?: string;
  description?: ReactNode;
  /** Name of the thing being deleted, woven into the default copy. */
  resourceName?: string;
  isPending?: boolean;
  confirmLabel?: string;
}

/** Reusable confirmation modal for destructive delete actions. */
export function ConfirmDeleteDialog({
  open,
  onOpenChange,
  onConfirm,
  title = 'Delete item',
  description,
  resourceName,
  isPending = false,
  confirmLabel = 'Delete',
}: ConfirmDeleteDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            {description ?? (
              <>
                Are you sure you want to delete
                {resourceName ? (
                  <>
                    {' '}
                    <span className="font-medium text-foreground">
                      {resourceName}
                    </span>
                  </>
                ) : (
                  ' this item'
                )}
                ? This action cannot be undone.
              </>
            )}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={isPending}
          >
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
