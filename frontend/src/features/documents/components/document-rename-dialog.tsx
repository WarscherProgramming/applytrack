import { Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

import type { DocumentConfig } from '../config';
import type { DocumentGroup } from '../types';

interface DocumentRenameDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: DocumentConfig;
  /** The document group being renamed (all versions are updated). */
  group: DocumentGroup | null;
}

export function DocumentRenameDialog({
  open,
  onOpenChange,
  config,
  group,
}: DocumentRenameDialogProps) {
  const { noun } = config;
  const { toast } = useToast();
  const rename = config.hooks.useRenameDocument();
  const [name, setName] = useState('');

  useEffect(() => {
    if (open && group) setName(group.name);
  }, [open, group]);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!group) return;
    const trimmed = name.trim();
    if (!trimmed) {
      toast({ variant: 'destructive', title: 'Name cannot be empty' });
      return;
    }
    if (trimmed === group.name) {
      onOpenChange(false);
      return;
    }
    rename.mutate(
      { ids: group.versions.map((v) => v.id), name: trimmed },
      {
        onSuccess: () => {
          toast({ title: `${noun} renamed`, description: trimmed });
          onOpenChange(false);
        },
        onError: (error) =>
          toast({
            variant: 'destructive',
            title: `Could not rename ${noun}`,
            description: getErrorMessage(error),
          }),
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Rename {noun}</DialogTitle>
          <DialogDescription>
            Renames every version of this {noun}.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="rename-name">Name</Label>
            <Input
              id="rename-name"
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={255}
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={rename.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={rename.isPending}>
              {rename.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
