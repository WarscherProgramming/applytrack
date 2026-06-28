import { Loader2 } from 'lucide-react';
import type { FormEvent } from 'react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';
import { humanizeEnum } from '@/utils/format';

import { TASK_PRIORITIES, TASK_STATUSES } from '../constants';
import { useCreateTask, useUpdateTask } from '../hooks';
import type { Task, TaskCreateInput, TaskPriority, TaskStatus } from '../types';

interface TaskFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task?: Task | null;
  defaultStatus?: TaskStatus;
}

interface FormState {
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string;
}

function emptyState(defaultStatus: TaskStatus = 'backlog'): FormState {
  return {
    title: '',
    description: '',
    status: defaultStatus,
    priority: 'medium',
    due_date: '',
  };
}

export function TaskFormDialog({
  open,
  onOpenChange,
  task,
  defaultStatus = 'backlog',
}: TaskFormDialogProps) {
  const isEdit = Boolean(task);
  const [values, setValues] = useState<FormState>(emptyState(defaultStatus));
  const { toast } = useToast();
  const createTask = useCreateTask();
  const updateTask = useUpdateTask();
  const isPending = createTask.isPending || updateTask.isPending;

  useEffect(() => {
    if (!open) return;
    setValues(
      task
        ? {
            title: task.title,
            description: task.description ?? '',
            status: task.status,
            priority: task.priority,
            due_date: task.due_date ?? '',
          }
        : emptyState(defaultStatus),
    );
  }, [open, task, defaultStatus]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload: TaskCreateInput = {
      title: values.title.trim(),
      description: values.description.trim() || null,
      status: values.status,
      priority: values.priority,
      due_date: values.due_date || null,
      source: task?.source ?? 'manual',
    };
    if (!payload.title) {
      toast({ variant: 'destructive', title: 'Task title is required' });
      return;
    }
    const onError = (error: unknown) =>
      toast({
        variant: 'destructive',
        title: isEdit ? 'Could not update task' : 'Could not create task',
        description: getErrorMessage(error),
      });

    if (task) {
      updateTask.mutate(
        { id: task.id, input: payload },
        {
          onSuccess: () => {
            toast({ title: 'Task updated' });
            onOpenChange(false);
          },
          onError,
        },
      );
      return;
    }
    createTask.mutate(payload, {
      onSuccess: () => {
        toast({ title: 'Task created' });
        onOpenChange(false);
      },
      onError,
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit task' : 'Create task'}</DialogTitle>
        </DialogHeader>
        <form className="space-y-4" onSubmit={submit}>
          <div className="space-y-2">
            <Label htmlFor="task-title">Title</Label>
            <Input
              id="task-title"
              value={values.title}
              onChange={(event) =>
                setValues((current) => ({ ...current, title: event.target.value }))
              }
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="task-description">Description</Label>
            <Textarea
              id="task-description"
              rows={4}
              value={values.description}
              onChange={(event) =>
                setValues((current) => ({
                  ...current,
                  description: event.target.value,
                }))
              }
            />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={values.status}
                onValueChange={(value) =>
                  setValues((current) => ({
                    ...current,
                    status: value as TaskStatus,
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TASK_STATUSES.map((status) => (
                    <SelectItem key={status} value={status}>
                      {humanizeEnum(status)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Priority</Label>
              <Select
                value={values.priority}
                onValueChange={(value) =>
                  setValues((current) => ({
                    ...current,
                    priority: value as TaskPriority,
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TASK_PRIORITIES.map((priority) => (
                    <SelectItem key={priority} value={priority}>
                      {humanizeEnum(priority)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="task-due-date">Due date</Label>
              <Input
                id="task-due-date"
                type="date"
                value={values.due_date}
                onChange={(event) =>
                  setValues((current) => ({
                    ...current,
                    due_date: event.target.value,
                  }))
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {isEdit ? 'Save changes' : 'Create task'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
