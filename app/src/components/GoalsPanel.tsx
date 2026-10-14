import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { CheckCircle2, CircleDot, Plus, Target } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';

interface Goal {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  status: 'active' | 'completed' | 'abandoned';
  parent_id: string | null;
  progress: { timestamp: string; note: string }[];
}

const priorityColors = { high: 'text-rose-300 border-rose-400/30', medium: 'text-amber-200 border-amber-400/30', low: 'text-cyan-200 border-cyan-400/30' };

export default function GoalsPanel() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [showCompleted, setShowCompleted] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<Goal['priority']>('medium');
  const [progressDrafts, setProgressDrafts] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState('');

  const loadGoals = async () => {
    const response = await fetch(`/api/goals?status=${showCompleted ? 'completed' : 'active'}`);
    const data = await response.json();
    setGoals(data.goals || []);
  };

  useEffect(() => { loadGoals().catch(() => setNotice('Unable to load goals.')); }, [showCompleted]);

  const createGoal = async (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim()) return;
    const response = await fetch('/api/goals', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description, priority }),
    });
    if (!response.ok) { setNotice('Unable to create goal.'); return; }
    setTitle(''); setDescription(''); setPriority('medium'); setNotice('Goal created.'); await loadGoals();
  };

  const updateGoal = async (goal: Goal, status?: Goal['status'], progress_note?: string) => {
    const response = await fetch(`/api/goals/${goal.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, progress_note }),
    });
    if (response.ok) await loadGoals();
  };

  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2"><Target className="h-5 w-5 text-amber-300" /><div><h2 className="text-lg font-semibold text-white">Goals</h2><p className="text-[10px] text-white/40">Sarah's commitments and progress</p></div></div>
          <Button onClick={() => setShowCompleted((value) => !value)} size="sm" variant="ghost" className="h-7 text-xs text-white/55">{showCompleted ? 'Active' : 'Completed'}</Button>
        </div>

        <Card className="border-white/10 bg-white/5 p-3">
          <form onSubmit={createGoal} className="space-y-2">
            <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="New goal title" className="border-white/10 bg-black/20 text-white placeholder:text-white/30" />
            <Textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Success criteria and context" className="min-h-16 border-white/10 bg-black/20 text-sm text-white placeholder:text-white/30" />
            <div className="flex items-center gap-2"><select value={priority} onChange={(event) => setPriority(event.target.value as Goal['priority'])} className="h-8 rounded-md border border-white/10 bg-black/30 px-2 text-xs text-white"><option value="high">High priority</option><option value="medium">Medium priority</option><option value="low">Low priority</option></select><Button type="submit" size="sm" className="ml-auto h-8 gap-1 bg-amber-500/15 text-amber-100 hover:bg-amber-500/25"><Plus className="h-3 w-3" /> Add goal</Button></div>
          </form>
        </Card>

        {notice && <p className="text-xs text-cyan-200">{notice}</p>}
        <div className="space-y-2">
          {goals.map((goal) => (
            <Card key={goal.id} className="border-white/10 bg-white/5 p-3">
              <div className="flex items-start gap-2"><button onClick={() => updateGoal(goal, 'completed')} title="Complete goal" className="mt-0.5 text-white/45 hover:text-emerald-300">{goal.status === 'completed' ? <CheckCircle2 className="h-4 w-4" /> : <CircleDot className="h-4 w-4" />}</button><div className="min-w-0 flex-1"><div className="flex items-center gap-2"><h3 className="text-sm font-medium text-white">{goal.title}</h3><Badge variant="outline" className={`text-[9px] ${priorityColors[goal.priority]}`}>{goal.priority}</Badge></div>{goal.description && <p className="mt-1 text-xs text-white/50">{goal.description}</p>}<p className="mt-2 text-[10px] text-white/30">{goal.progress.length} progress entr{goal.progress.length === 1 ? 'y' : 'ies'}</p>{goal.progress.slice(-2).map((entry) => <p key={entry.timestamp} className="mt-1 border-l border-amber-400/30 pl-2 text-xs text-white/55">{entry.note}</p>)}<div className="mt-2 flex gap-2"><Input value={progressDrafts[goal.id] || ''} onChange={(event) => setProgressDrafts((current) => ({ ...current, [goal.id]: event.target.value }))} placeholder="Add progress note" className="h-7 border-white/10 bg-black/20 text-xs text-white placeholder:text-white/25" /><Button onClick={() => { const note = progressDrafts[goal.id]?.trim(); if (note) { updateGoal(goal, undefined, note); setProgressDrafts((current) => ({ ...current, [goal.id]: '' })); } }} size="sm" variant="ghost" className="h-7 shrink-0 text-xs text-amber-200">Log</Button></div></div></div>
            </Card>
          ))}
          {goals.length === 0 && <p className="py-8 text-center text-sm text-white/30">No {showCompleted ? 'completed' : 'active'} goals yet.</p>}
        </div>
      </div>
    </ScrollArea>
  );
}
