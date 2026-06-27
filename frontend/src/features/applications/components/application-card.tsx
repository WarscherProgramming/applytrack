import {
  Building2,
  CalendarDays,
  DollarSign,
  FileSignature,
  FileText,
  GripVertical,
  MapPin,
  MoreHorizontal,
  Pencil,
  Tag,
  Trash2,
} from 'lucide-react';
import type { DragEvent } from 'react';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { formatDate, humanizeEnum } from '@/utils/format';

import { APPLICATION_STATUSES } from '../constants';
import type { Application } from '../types/application.types';

interface ApplicationCardProps {
  application: Application;
  companyName?: string;
  onEdit: (application: Application) => void;
  onDelete: (application: Application) => void;
  onMove: (application: Application, status: Application['status']) => void;
  /** True while a status change for this card is in flight. */
  isUpdating?: boolean;
  onDragStart: (event: DragEvent, application: Application) => void;
  onDragEnd: () => void;
  isDragging?: boolean;
}

/**
 * A single application on the board. Shows the key fields and exposes status
 * changes two ways: the "Move to" menu (accessible/keyboard) and native
 * HTML5 drag (the GripVertical handle hints draggability).
 */
export function ApplicationCard({
  application,
  companyName,
  onEdit,
  onDelete,
  onMove,
  isUpdating = false,
  onDragStart,
  onDragEnd,
  isDragging = false,
}: ApplicationCardProps) {
  const {
    job_title,
    location,
    salary_range,
    date_applied,
    source,
    notes,
    resume_id,
    cover_letter_id,
  } = application;

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, application)}
      onDragEnd={onDragEnd}
      className={cn(
        'group rounded-lg border bg-card p-3 shadow-sm transition-shadow hover:shadow-md',
        isDragging && 'opacity-50',
        isUpdating && 'pointer-events-none opacity-60',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-start gap-1.5">
          <GripVertical className="mt-0.5 h-4 w-4 shrink-0 cursor-grab text-muted-foreground/50 group-hover:text-muted-foreground" />
          <div className="min-w-0">
            <p className="truncate text-sm font-medium leading-snug">{job_title}</p>
            <p className="flex items-center gap-1 truncate text-xs text-muted-foreground">
              <Building2 className="h-3 w-3 shrink-0" />
              {companyName ?? 'Unknown company'}
            </p>
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 shrink-0"
              aria-label={`Actions for ${job_title}`}
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={() => onEdit(application)}>
              <Pencil className="h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => onDelete(application)}
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
              Move to
            </DropdownMenuLabel>
            {APPLICATION_STATUSES.filter((s) => s !== application.status).map(
              (status) => (
                <DropdownMenuItem
                  key={status}
                  onClick={() => onMove(application, status)}
                >
                  {humanizeEnum(status)}
                </DropdownMenuItem>
              ),
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="mt-2 space-y-1 pl-[22px]">
        {location ? (
          <p className="flex items-center gap-1.5 truncate text-xs text-muted-foreground">
            <MapPin className="h-3 w-3 shrink-0" />
            {location}
          </p>
        ) : null}
        {salary_range ? (
          <p className="flex items-center gap-1.5 truncate text-xs text-muted-foreground">
            <DollarSign className="h-3 w-3 shrink-0" />
            {salary_range}
          </p>
        ) : null}
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {date_applied ? (
            <span className="flex items-center gap-1.5">
              <CalendarDays className="h-3 w-3 shrink-0" />
              {formatDate(date_applied)}
            </span>
          ) : null}
          {source ? (
            <span className="flex items-center gap-1.5 truncate">
              <Tag className="h-3 w-3 shrink-0" />
              {source}
            </span>
          ) : null}
        </div>
        {notes ? (
          <p className="line-clamp-2 pt-0.5 text-xs text-muted-foreground/80">
            {notes}
          </p>
        ) : null}
        {resume_id || cover_letter_id ? (
          <div className="flex items-center gap-3 pt-0.5 text-xs text-muted-foreground">
            {resume_id ? (
              <span
                className="flex items-center gap-1.5"
                title="Resume submitted"
              >
                <FileText className="h-3 w-3 shrink-0" />
                Resume
              </span>
            ) : null}
            {cover_letter_id ? (
              <span
                className="flex items-center gap-1.5"
                title="Cover letter submitted"
              >
                <FileSignature className="h-3 w-3 shrink-0" />
                Cover letter
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
