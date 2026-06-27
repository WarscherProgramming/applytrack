import {
  ChevronDown,
  Download,
  FileText,
  History,
  MoreHorizontal,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { formatDate } from '@/utils/format';

import type { DocumentConfig } from '../config';
import { fileExtensionLabel, triggerDownload } from '../lib';
import type { DocumentGroup, DocumentItem } from '../types';

interface DocumentGroupCardProps {
  group: DocumentGroup;
  config: DocumentConfig;
  onUploadVersion: (name: string) => void;
  onRename: (group: DocumentGroup) => void;
  onDeleteGroup: (group: DocumentGroup) => void;
  onDeleteVersion: (version: DocumentItem) => void;
}

export function DocumentGroupCard({
  group,
  config,
  onUploadVersion,
  onRename,
  onDeleteGroup,
  onDeleteVersion,
}: DocumentGroupCardProps) {
  const [expanded, setExpanded] = useState(false);
  const { latest, versions } = group;
  const hasHistory = versions.length > 1;

  function download(doc: DocumentItem) {
    triggerDownload(config.api.downloadUrl(doc.id), doc.file_name);
  }

  return (
    <Card>
      <CardContent className="p-4 sm:p-5">
        <div className="flex items-start gap-4">
          <div className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary sm:flex">
            <FileText className="h-5 w-5" />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="truncate font-semibold">{group.name}</h3>
              <Badge variant="secondary">v{latest.version}</Badge>
              <Badge variant="outline">{fileExtensionLabel(latest.file_name)}</Badge>
            </div>
            <p className="mt-1 truncate text-sm text-muted-foreground">
              {latest.file_name}
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Updated {formatDate(latest.updated_at)}
              {versions.length > 1 ? ` · ${versions.length} versions` : null}
            </p>
            {latest.notes ? (
              <p className="mt-2 text-sm text-muted-foreground">{latest.notes}</p>
            ) : null}
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => download(latest)}
              title="Download latest version"
            >
              <Download className="h-4 w-4" />
              <span className="hidden sm:inline">Download</span>
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9"
                  aria-label={`Actions for ${group.name}`}
                >
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onUploadVersion(group.name)}>
                  <Plus className="h-4 w-4" />
                  Upload new version
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onRename(group)}>
                  <Pencil className="h-4 w-4" />
                  Rename
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={() => onDeleteGroup(group)}
                >
                  <Trash2 className="h-4 w-4" />
                  Delete {config.noun}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {hasHistory ? (
          <div className="mt-3 border-t pt-3">
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground"
              aria-expanded={expanded}
            >
              <History className="h-4 w-4" />
              Version history
              <ChevronDown
                className={cn(
                  'h-4 w-4 transition-transform',
                  expanded && 'rotate-180',
                )}
              />
            </button>

            {expanded ? (
              <ul className="mt-3 space-y-2">
                {versions.map((version) => (
                  <li
                    key={version.id}
                    className="flex items-center gap-3 rounded-lg border bg-muted/30 px-3 py-2"
                  >
                    <Badge variant="secondary" className="shrink-0">
                      v{version.version}
                    </Badge>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {version.file_name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Uploaded {formatDate(version.created_at)}
                        {version.notes ? ` · ${version.notes}` : null}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      aria-label={`Download version ${version.version}`}
                      onClick={() => download(version)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      aria-label={`Delete version ${version.version}`}
                      onClick={() => onDeleteVersion(version)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
