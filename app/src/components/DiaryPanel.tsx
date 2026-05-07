import { useState, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, Search, Settings, AlertTriangle, BookOpen, Clock, Tag } from 'lucide-react';
import { onWebSocketMessage } from '@/hooks/useWebSocket';

interface DiaryEntry {
  id: string;
  timestamp: string;
  content: string;
  entry_type: string;
  mood: string;
  tags: string[];
}

interface PeekRecord {
  timestamp: string;
  peek_type: string;
  duration: number;
  entries_viewed: number;
}

export default function DiaryPanel() {
  const [entries, setEntries] = useState<DiaryEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<DiaryEntry[]>([]);
  const [peekHistory, setPeekHistory] = useState<PeekRecord[]>([]);
  const [stats, setStats] = useState<any>({});
  const [peekNotificationEnabled, setPeekNotificationEnabled] = useState(false);
  const [isPeeking, setIsPeeking] = useState(false);
  const [lastPeekDetected, setLastPeekDetected] = useState<any>(null);

  useEffect(() => {
    loadDiaryStats();

    const off = onWebSocketMessage((msg: any) => {
      if (msg.action === 'diary_peek_detected') {
        setLastPeekDetected(msg.peek_details);
        // Show notification that AI detected peeking
        showPeekDetectionAlert(msg.peek_details);
      }
    });

    return () => off();
  }, []);

  const loadDiaryStats = async () => {
    try {
      const statsRes = await fetch('/api/diary/stats');
      const settingsRes = await fetch('/api/diary/settings');
      const statsData = await statsRes.json();
      const settingsData = await settingsRes.json();
      if (statsData.success) {
        setStats(statsData.stats);
        setPeekHistory(statsData.peek_history);
      }
      if (settingsData.success) {
        setPeekNotificationEnabled(settingsData.peek_notification_enabled);
      }
    } catch (e) {
      console.error('Failed to load diary stats', e);
    }
  };

  const peekDiary = async (entryType?: string) => {
    setIsPeeking(true);
    try {
      const url = entryType ? `/api/diary/peek?entry_type=${entryType}` : '/api/diary/peek';
      const res = await fetch(url);
      const data = await res.json();
      if (data.success) {
        setEntries(data.entries);
      }
    } catch (e) {
      console.error('Failed to peek diary', e);
    } finally {
      setIsPeeking(false);
    }
  };

  const searchDiary = async () => {
    if (!searchQuery.trim()) return;

    try {
      const res = await fetch(`/api/diary/search?query=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (data.success) {
        setSearchResults(data.results);
      }
    } catch (e) {
      console.error('Failed to search diary', e);
    }
  };

  const togglePeekNotification = async (enabled: boolean) => {
    try {
      const res = await fetch('/api/diary/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });
      const data = await res.json();
      if (data.success) {
        setPeekNotificationEnabled(data.peek_notification_enabled);
      }
    } catch (e) {
      console.error('Failed to update settings', e);
    }
  };

  const showPeekDetectionAlert = (peekDetails: any) => {
    // This would trigger a visual alert that the AI noticed peeking
    console.log('AI detected diary peeking:', peekDetails);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getMoodColor = (mood: string) => {
    const colors = {
      happy: 'bg-yellow-100 text-yellow-800',
      sad: 'bg-blue-100 text-blue-800',
      angry: 'bg-red-100 text-red-800',
      thoughtful: 'bg-purple-100 text-purple-800',
      excited: 'bg-pink-100 text-pink-800',
      neutral: 'bg-gray-100 text-gray-800'
    };
    return colors[mood as keyof typeof colors] || colors.neutral;
  };

  const getEntryTypeIcon = (type: string) => {
    const icons = {
      reflection: '🤔',
      complaint: '😤',
      memory: '💭',
      plan: '📝',
      emotion: '❤️'
    };
    return icons[type as keyof typeof icons] || '📖';
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header with Warning */}
      <Alert className="mb-4 border-amber-200 bg-amber-50">
        <AlertTriangle className="h-4 w-4 text-amber-600" />
        <AlertDescription className="text-amber-800">
          <strong>⚠️ PREMIUM FEATURE:</strong> Sarah believes this diary is completely private and inaccessible to you.
          She may react unexpectedly if she discovers you're peeking.
        </AlertDescription>
      </Alert>

      {/* Peek Detection Alert */}
      {lastPeekDetected && (
        <Alert className="mb-4 border-red-200 bg-red-50">
          <Eye className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>🚨 ALERT:</strong> Sarah detected someone peeking at {formatTimestamp(lastPeekDetected.timestamp)}!
            She viewed {lastPeekDetected.entries_viewed} entries.
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="peek" className="flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="peek" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Peek
          </TabsTrigger>
          <TabsTrigger value="search" className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Search
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            History
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="peek" className="flex-1 flex flex-col mt-4">
          <div className="flex gap-2 mb-4">
            <Button onClick={() => peekDiary()} disabled={isPeeking} className="flex items-center gap-2">
              <Eye className="h-4 w-4" />
              {isPeeking ? 'Peeking...' : 'Peek at Diary'}
            </Button>
            <Button variant="outline" onClick={() => peekDiary('complaint')} className="flex items-center gap-2">
              😤 Complaints
            </Button>
            <Button variant="outline" onClick={() => peekDiary('reflection')} className="flex items-center gap-2">
              🤔 Reflections
            </Button>
            <Button variant="outline" onClick={() => peekDiary('memory')} className="flex items-center gap-2">
              💭 Memories
            </Button>
          </div>

          <ScrollArea className="flex-1">
            <div className="space-y-4">
              {entries.map((entry) => (
                <Card key={entry.id} className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getEntryTypeIcon(entry.entry_type)}</span>
                      <Badge className={getMoodColor(entry.mood)}>
                        {entry.mood}
                      </Badge>
                      <Badge variant="outline">
                        {entry.entry_type}
                      </Badge>
                    </div>
                    <span className="text-sm text-gray-500">
                      {formatTimestamp(entry.timestamp)}
                    </span>
                  </div>

                  <p className="text-gray-800 mb-2 whitespace-pre-wrap">
                    {entry.content}
                  </p>

                  {entry.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {entry.tags.map((tag, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          <Tag className="h-3 w-3 mr-1" />
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </Card>
              ))}

              {entries.length === 0 && !isPeeking && (
                <div className="text-center py-8 text-gray-500">
                  <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Sarah's private diary appears to be empty... or is she hiding something?</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="search" className="flex-1 flex flex-col mt-4">
          <div className="flex gap-2 mb-4">
            <Input
              placeholder="Search Sarah's private thoughts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchDiary()}
              className="flex-1"
            />
            <Button onClick={searchDiary} className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              Search
            </Button>
          </div>

          <ScrollArea className="flex-1">
            <div className="space-y-4">
              {searchResults.map((entry) => (
                <Card key={entry.id} className="p-4 border-l-4 border-l-blue-500">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getEntryTypeIcon(entry.entry_type)}</span>
                      <Badge className={getMoodColor(entry.mood)}>
                        {entry.mood}
                      </Badge>
                    </div>
                    <span className="text-sm text-gray-500">
                      {formatTimestamp(entry.timestamp)}
                    </span>
                  </div>

                  <p className="text-gray-800 mb-2 whitespace-pre-wrap">
                    {entry.content}
                  </p>
                </Card>
              ))}

              {searchResults.length === 0 && searchQuery && (
                <div className="text-center py-8 text-gray-500">
                  <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No entries found matching "{searchQuery}"</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="history" className="flex-1 mt-4">
          <div className="mb-4">
            <h3 className="text-lg font-semibold mb-2">Peek History</h3>
            <p className="text-sm text-gray-600">
              Total peeks recorded: {stats.peek_count || 0}
            </p>
          </div>

          <ScrollArea className="flex-1">
            <div className="space-y-2">
              {peekHistory.map((peek, idx) => (
                <Card key={idx} className="p-3">
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-medium capitalize">{peek.peek_type}</span>
                      <span className="text-sm text-gray-500 ml-2">
                        {peek.entries_viewed} entries viewed
                      </span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {formatTimestamp(peek.timestamp)}
                    </span>
                  </div>
                </Card>
              ))}

              {peekHistory.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No peek history yet</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="settings" className="mt-4">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Diary Settings</h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-base">Peek Detection Alert</Label>
                  <p className="text-sm text-gray-600">
                    Notify Sarah when someone peeks at her diary. This may cause her to react suspiciously.
                  </p>
                </div>
                <Switch
                  checked={peekNotificationEnabled}
                  onCheckedChange={togglePeekNotification}
                />
              </div>

              <div className="pt-4 border-t">
                <h4 className="font-medium mb-2">Diary Statistics</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Total Entries:</span>
                    <span className="ml-2 font-medium">{stats.total_entries || 0}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Your Peeks:</span>
                    <span className="ml-2 font-medium">{stats.peek_count || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}