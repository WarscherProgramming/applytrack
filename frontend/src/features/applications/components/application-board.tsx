import { useMemo, useState, type DragEvent } from 'react';

import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';
import { humanizeEnum } from '@/utils/format';

import { APPLICATION_STATUSES } from '../constants';
import { useUpdateApplication } from '../hooks/use-applications';
import type { Application, ApplicationStatus } from '../types/application.types';
import { ApplicationColumn } from './application-column';

interface ApplicationBoardProps {
  applications: Application[];
  companyById: Map<string, string>;
  onEdit: (application: Application) => void;
  onDelete: (application: Application) => void;
}

/**
 * The Kanban board. Groups applications into status columns and owns the
 * status-change interaction — both the card "Move to" menu and native HTML5
 * drag-and-drop funnel through `moveTo`, which PATCHes the backend; the shared
 * list query then refetches and re-groups the board.
 */
export function ApplicationBoard({
  applications,
  companyById,
  onEdit,
  onDelete,
}: ApplicationBoardProps) {
  const { toast } = useToast();
  const updateApplication = useUpdateApplication();

  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [overStatus, setOverStatus] = useState<ApplicationStatus | null>(null);

  // Group once per data change; every status gets a column even when empty.
  const { grouped, byId } = useMemo(() => {
    const grouped = new Map<ApplicationStatus, Application[]>();
    for (const status of APPLICATION_STATUSES) grouped.set(status, []);
    const byId = new Map<string, Application>();
    for (const app of applications) {
      grouped.get(app.status)?.push(app);
      byId.set(app.id, app);
    }
    return { grouped, byId };
  }, [applications]);

  function moveTo(application: Application, status: ApplicationStatus) {
    if (application.status === status) return;
    updateApplication.mutate(
      { id: application.id, input: { status } },
      {
        onSuccess: () =>
          toast({
            title: 'Status updated',
            description: `${application.job_title} → ${humanizeEnum(status)}`,
          }),
        onError: (error) =>
          toast({
            variant: 'destructive',
            title: 'Could not update status',
            description: getErrorMessage(error),
          }),
      },
    );
  }

  function onCardDragStart(event: DragEvent, application: Application) {
    event.dataTransfer.setData('text/plain', application.id);
    event.dataTransfer.effectAllowed = 'move';
    setDraggingId(application.id);
  }

  function onCardDragEnd() {
    setDraggingId(null);
    setOverStatus(null);
  }

  function onColumnDragOver(event: DragEvent, status: ApplicationStatus) {
    event.preventDefault(); // Required to allow a drop.
    event.dataTransfer.dropEffect = 'move';
    if (overStatus !== status) setOverStatus(status);
  }

  function onColumnDrop(event: DragEvent, status: ApplicationStatus) {
    event.preventDefault();
    const id = event.dataTransfer.getData('text/plain');
    setDraggingId(null);
    setOverStatus(null);
    const application = byId.get(id);
    if (application) moveTo(application, status);
  }

  const updatingId = updateApplication.isPending
    ? (updateApplication.variables?.id ?? null)
    : null;

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {APPLICATION_STATUSES.map((status) => (
        <ApplicationColumn
          key={status}
          status={status}
          applications={grouped.get(status) ?? []}
          companyById={companyById}
          isOver={overStatus === status}
          draggingId={draggingId}
          updatingId={updatingId}
          onEdit={onEdit}
          onDelete={onDelete}
          onMove={moveTo}
          onCardDragStart={onCardDragStart}
          onCardDragEnd={onCardDragEnd}
          onColumnDragOver={onColumnDragOver}
          onColumnDragLeave={() => {}}
          onColumnDrop={onColumnDrop}
        />
      ))}
    </div>
  );
}
