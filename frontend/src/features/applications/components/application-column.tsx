import type { DragEvent } from 'react';

import { cn } from '@/lib/utils';
import { humanizeEnum } from '@/utils/format';

import type { Application, ApplicationStatus } from '../types/application.types';
import { ApplicationCard } from './application-card';

interface ApplicationColumnProps {
  status: ApplicationStatus;
  applications: Application[];
  companyById: Map<string, string>;
  /** True while a card is being dragged over this column. */
  isOver: boolean;
  draggingId: string | null;
  updatingId: string | null;
  onEdit: (application: Application) => void;
  onDelete: (application: Application) => void;
  onMove: (application: Application, status: ApplicationStatus) => void;
  onCardDragStart: (event: DragEvent, application: Application) => void;
  onCardDragEnd: () => void;
  onColumnDragOver: (event: DragEvent, status: ApplicationStatus) => void;
  onColumnDragLeave: (event: DragEvent) => void;
  onColumnDrop: (event: DragEvent, status: ApplicationStatus) => void;
}

/** One Kanban column: a status header, a count, and its cards (a drop target). */
export function ApplicationColumn({
  status,
  applications,
  companyById,
  isOver,
  draggingId,
  updatingId,
  onEdit,
  onDelete,
  onMove,
  onCardDragStart,
  onCardDragEnd,
  onColumnDragOver,
  onColumnDragLeave,
  onColumnDrop,
}: ApplicationColumnProps) {
  return (
    <div className="flex w-72 shrink-0 flex-col">
      <div className="mb-2 flex items-center justify-between px-1">
        <h3 className="text-sm font-medium">{humanizeEnum(status)}</h3>
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {applications.length}
        </span>
      </div>

      <div
        onDragOver={(e) => onColumnDragOver(e, status)}
        onDragLeave={onColumnDragLeave}
        onDrop={(e) => onColumnDrop(e, status)}
        className={cn(
          'flex flex-1 flex-col gap-2 rounded-lg border border-dashed border-transparent bg-muted/40 p-2 transition-colors',
          isOver && 'border-primary/50 bg-primary/5',
        )}
      >
        {applications.length === 0 ? (
          <p className="px-2 py-6 text-center text-xs text-muted-foreground">
            {isOver ? 'Drop here' : 'No applications'}
          </p>
        ) : (
          applications.map((application) => (
            <ApplicationCard
              key={application.id}
              application={application}
              companyName={companyById.get(application.company_id)}
              onEdit={onEdit}
              onDelete={onDelete}
              onMove={onMove}
              isUpdating={updatingId === application.id}
              isDragging={draggingId === application.id}
              onDragStart={onCardDragStart}
              onDragEnd={onCardDragEnd}
            />
          ))
        )}
      </div>
    </div>
  );
}
