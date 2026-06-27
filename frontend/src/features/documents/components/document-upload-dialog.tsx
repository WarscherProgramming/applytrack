import { Loader2, UploadCloud } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

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
import { Textarea } from '@/components/ui/textarea';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

import type { DocumentConfig } from '../config';

/** File extensions the backend accepts (kept in sync with ALLOWED_EXTENSIONS). */
const ACCEPT = '.pdf,.doc,.docx,.txt,.rtf,.odt,.md';

interface DocumentUploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: DocumentConfig;
  /**
   * When set, the dialog uploads a new version of this existing document: the
   * name is fixed to presetName. When null, it creates a brand-new document.
   */
  presetName?: string | null;
}

export function DocumentUploadDialog({
  open,
  onOpenChange,
  config,
  presetName = null,
}: DocumentUploadDialogProps) {
  const { noun } = config;
  const { toast } = useToast();
  const upload = config.hooks.useUploadDocument();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [notes, setNotes] = useState('');

  const isVersion = presetName !== null;

  // Reset fields each time the dialog opens.
  useEffect(() => {
    if (!open) return;
    setFile(null);
    setName('');
    setNotes('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [open]);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) {
      toast({ variant: 'destructive', title: 'Choose a file to upload' });
      return;
    }
    upload.mutate(
      {
        file,
        // Version mode locks the name to the group; new mode falls back to the
        // file's base name server-side when left blank.
        name: isVersion ? (presetName ?? undefined) : name.trim() || undefined,
        notes: notes.trim() || undefined,
      },
      {
        onSuccess: (doc) => {
          toast({
            title: isVersion ? 'New version uploaded' : `${noun} uploaded`,
            description: `${doc.name} · v${doc.version}`,
          });
          onOpenChange(false);
        },
        onError: (error) =>
          toast({
            variant: 'destructive',
            title: `Could not upload ${noun}`,
            description: getErrorMessage(error),
          }),
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {isVersion ? `Upload new version` : `Upload ${noun}`}
          </DialogTitle>
          <DialogDescription>
            {isVersion ? (
              <>
                Add a new version to{' '}
                <span className="font-medium text-foreground">{presetName}</span>.
              </>
            ) : (
              `PDF, Word, text, RTF, ODT, or Markdown. Up to 10 MB.`
            )}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="document-file">
              File <span className="text-destructive">*</span>
            </Label>
            <Input
              id="document-file"
              ref={fileInputRef}
              type="file"
              accept={ACCEPT}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="cursor-pointer file:mr-3 file:cursor-pointer file:rounded file:border-0 file:bg-muted file:px-3 file:py-1 file:text-sm"
            />
          </div>

          {!isVersion ? (
            <div className="space-y-2">
              <Label htmlFor="document-name">Name</Label>
              <Input
                id="document-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Defaults to the file name"
                maxLength={255}
              />
              <p className="text-xs text-muted-foreground">
                Versions sharing a name are grouped together.
              </p>
            </div>
          ) : null}

          <div className="space-y-2">
            <Label htmlFor="document-notes">Notes</Label>
            <Textarea
              id="document-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Optional — e.g. tailored for backend roles"
              maxLength={5000}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={upload.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={upload.isPending}>
              {upload.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <UploadCloud className="h-4 w-4" />
              )}
              Upload
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
