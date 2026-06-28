import { format, isBefore, parseISO, startOfToday } from 'date-fns';
import {
  CheckCircle2,
  Loader2,
  Plus,
  Sparkles,
  Trash2,
  XCircle,
} from 'lucide-react';
import { useMemo, useState } from 'react';

import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import { PageHeader } from '@/components/common/page-header';
import { PriorityBadge } from '@/components/common/priority-badge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { TaskFormDialog } from '@/features/tasks/components/task-form-dialog';
import { TASK_PRIORITIES, TASK_SOURCES, TASK_VIEWS } from '@/features/tasks/constants';
import {
  useCompleteTask,
  useDeleteTask,
  useDismissTask,
  useGenerateTasks,
  useTasks,
} from '@/features/tasks/hooks';
import type { Task, TaskPriority, TaskSource, TaskStatus } from '@/features/tasks/types';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';
import { humanizeEnum } from '@/utils/format';

const ALL = 'all';

export function TasksPage() {
  const [view, setView] = useState<TaskStatus>('today');
  const [priority, setPriority] = useState<TaskPriority | typeof ALL>(ALL);
  const [source, setSource] = useState<TaskSource | typeof ALL>(ALL);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Task | null>(null);
  const { toast } = useToast();

  const params = useMemo(
    () => ({
      status: view,
      priority: priority === ALL ? undefined : priority,
      source: source === ALL ? undefined : source,
      limit: 100,
    }),
    [view, priority, source],
  );
  const tasks = useTasks(params);
  const completeTask = useCompleteTask();
  const dismissTask = useDismissTask();
  const deleteTask = useDeleteTask();
  const generateTasks = useGenerateTasks();

  function openCreate() {
    setEditing(null);
    setDialogOpen(true);
  }

  function openEdit(task: Task) {
    setEditing(task);
    setDialogOpen(true);
  }

  function generate() {
    generateTasks.mutate(undefined, {
      onSuccess: (result) =>
        toast({
          title: 'Tasks generated',
          description: `${result.created} created, ${result.updated} refreshed, ${result.skipped} skipped.`,
        }),
      onError: (error) =>
        toast({
          variant: 'destructive',
          title: 'Task generation failed',
          description: getErrorMessage(error),
        }),
    });
  }

  const items = tasks.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tasks"
        description="Turn ApplyTrack insights into focused job-search work."
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={generate}
              disabled={generateTasks.isPending}
            >
              {generateTasks.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Generate
            </Button>
            <Button size="sm" onClick={openCreate}>
              <Plus className="h-4 w-4" />
              New task
            </Button>
          </>
        }
      />

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="grid grid-cols-2 gap-2 md:flex">
          {TASK_VIEWS.map((status) => (
            <Button
              key={status}
              variant={view === status ? 'default' : 'outline'}
              size="sm"
              onClick={() => setView(status)}
            >
              {humanizeEnum(status)}
            </Button>
          ))}
        </div>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <Select
            value={priority}
            onValueChange={(value) => setPriority(value as TaskPriority | typeof ALL)}
          >
            <SelectTrigger className="min-w-40">
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>All priorities</SelectItem>
              {TASK_PRIORITIES.map((item) => (
                <SelectItem key={item} value={item}>
                  {humanizeEnum(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={source}
            onValueChange={(value) => setSource(value as TaskSource | typeof ALL)}
          >
            <SelectTrigger className="min-w-44">
              <SelectValue placeholder="Source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>All sources</SelectItem>
              {TASK_SOURCES.map((item) => (
                <SelectItem key={item} value={item}>
                  {humanizeEnum(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {tasks.isError ? (
        <ErrorState error={tasks.error} onRetry={() => tasks.refetch()} />
      ) : tasks.isLoading ? (
        <TaskSkeleton />
      ) : items.length ? (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
          {items.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onEdit={() => openEdit(task)}
              onComplete={() =>
                completeTask.mutate(task.id, {
                  onSuccess: () => toast({ title: 'Task completed' }),
                })
              }
              onDismiss={() =>
                dismissTask.mutate(task.id, {
                  onSuccess: () => toast({ title: 'Task dismissed' }),
                })
              }
              onDelete={() =>
                deleteTask.mutate(task.id, {
                  onSuccess: () => toast({ title: 'Task deleted' }),
                })
              }
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No tasks here"
          description="Create a manual task or generate tasks from your current ApplyTrack activity."
          action={
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" />
              New task
            </Button>
          }
        />
      )}

      <TaskFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        task={editing}
        defaultStatus={view}
      />
    </div>
  );
}

function TaskCard({
  task,
  onEdit,
  onComplete,
  onDismiss,
  onDelete,
}: {
  task: Task;
  onEdit: () => void;
  onComplete: () => void;
  onDismiss: () => void;
  onDelete: () => void;
}) {
  const overdue =
    task.due_date && isBefore(parseISO(task.due_date), startOfToday()) && task.status !== 'completed';
  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="text-base">{task.title}</CardTitle>
            <CardDescription className="mt-1">
              {task.description || 'No description'}
            </CardDescription>
          </div>
          <PriorityBadge priority={task.priority} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">{humanizeEnum(task.source)}</Badge>
          {task.due_date ? (
            <Badge variant={overdue ? 'destructive' : 'secondary'}>
              {overdue ? 'Overdue ' : ''}
              {format(parseISO(task.due_date), 'MMM d')}
            </Badge>
          ) : (
            <Badge variant="secondary">No due date</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={onEdit}>
          Edit
        </Button>
        {task.status !== 'completed' ? (
          <Button size="sm" variant="outline" onClick={onComplete}>
            <CheckCircle2 className="h-4 w-4" />
            Complete
          </Button>
        ) : null}
        {task.status !== 'dismissed' ? (
          <Button size="sm" variant="outline" onClick={onDismiss}>
            <XCircle className="h-4 w-4" />
            Dismiss
          </Button>
        ) : null}
        <Button
          size="sm"
          variant="outline"
          className="text-destructive hover:text-destructive"
          onClick={onDelete}
        >
          <Trash2 className="h-4 w-4" />
          Delete
        </Button>
      </CardContent>
    </Card>
  );
}

function TaskSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <Skeleton key={index} className="h-48 w-full" />
      ))}
    </div>
  );
}
