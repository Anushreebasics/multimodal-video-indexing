"use client";

import React, { useState, useEffect } from 'react';

interface Event {
    timestamp: number;
    type: string;
    score: number;
    importance: number;
    description: string;
}

interface Summary {
    top_moments: number[];
    event_count: number;
    scene_count: number;
    audio_spike_count?: number;
    highlight_description: string;
}

interface TimelineProps {
    videoId: string | null;
    onSeek: (timestamp: number) => void;
}

export default function EventTimeline({ videoId, onSeek }: TimelineProps) {
    const [events, setEvents] = useState<Event[]>([]);
    const [summary, setSummary] = useState<Summary | null>(null);
    const [loading, setLoading] = useState(false);
    const [selectedType, setSelectedType] = useState<string>('all');

    useEffect(() => {
        if (videoId) {
            loadEvents();
        }
    }, [videoId]);

    const loadEvents = async () => {
        if (!videoId) return;

        setLoading(true);
        try {
            console.log('Loading events for video:', videoId);
            const response = await fetch(`http://localhost:8000/api/events/${videoId}`);
            console.log('Events response status:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Events data:', data);

            setEvents(data.events || []);
            setSummary(data.summary || null);
        } catch (error) {
            console.error('Error loading events:', error);
            setEvents([]);
            setSummary(null);
        } finally {
            setLoading(false);
        }
    };

    if (!videoId) {
        return <p className="text-gray-500 text-center py-8">Upload a video to see event timeline</p>;
    }

    if (loading) {
        return <div className="text-center py-4">Loading timeline...</div>;
    }

    if (!events || events.length === 0) {
        return (
            <div className="text-center py-8">
                <p className="text-gray-500 mb-2">No events detected in this video</p>
                <p className="text-xs text-gray-400">Try uploading a video with scene changes or audio highlights</p>
            </div>
        );
    }

    const eventTypes = ['all', ...new Set(events.map(e => e.type))];
    const filteredEvents = selectedType === 'all'
        ? events
        : events.filter(e => e.type === selectedType);

    const getEventColor = (type: string) => {
        switch (type) {
            case 'scene_change': return 'bg-blue-500';
            case 'audio_spike': return 'bg-red-500';
            case 'silence': return 'bg-gray-400';
            case 'entity_mention': return 'bg-purple-500';
            default: return 'bg-green-500';
        }
    };

    const getEventIcon = (type: string) => {
        switch (type) {
            case 'scene_change': return '🎬';
            case 'audio_spike': return '🔊';
            case 'silence': return '🔇';
            case 'entity_mention': return '📌';
            default: return '⭐';
        }
    };

    return (
        <div className="space-y-4">
            {/* Summary Card */}
            {summary && (
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border border-blue-200">
                    <h4 className="font-semibold text-gray-900 mb-2">Video Summary</h4>
                    <p className="text-sm text-gray-700 mb-2">{summary.highlight_description}</p>
                    <div className="flex gap-4 text-xs text-gray-600">
                        <span>📊 {summary.event_count} events</span>
                        <span>🎬 {summary.scene_count} scenes</span>
                        {summary.audio_spike_count && <span>🔊 {summary.audio_spike_count} audio highlights</span>}
                    </div>
                </div>
            )}

            {/* Event Type Filter */}
            <div className="flex gap-2 flex-wrap">
                {eventTypes.map(type => (
                    <button
                        key={type}
                        onClick={() => setSelectedType(type)}
                        className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${selectedType === type
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        {type.toUpperCase().replace('_', ' ')}
                    </button>
                ))}
            </div>

            {/* Top Moments */}
            {summary && summary.top_moments && summary.top_moments.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <h5 className="font-semibold text-yellow-900 text-sm mb-2">⭐ Top Highlights</h5>
                    <div className="flex gap-2 flex-wrap">
                        {summary.top_moments.slice(0, 5).map((timestamp, idx) => (
                            <button
                                key={idx}
                                onClick={() => onSeek(timestamp)}
                                className="px-3 py-1 bg-yellow-600 text-white rounded-full text-xs font-semibold hover:bg-yellow-700 transition-colors"
                            >
                                #{idx + 1} @ {new Date(timestamp * 1000).toISOString().substr(14, 5)}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Event Timeline */}
            <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredEvents.map((event, idx) => (
                    <div
                        key={idx}
                        onClick={() => onSeek(event.timestamp)}
                        className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors cursor-pointer"
                    >
                        <div className="flex items-start gap-3">
                            <span className="text-2xl">{getEventIcon(event.type)}</span>
                            <div className="flex-1">
                                <div className="flex justify-between items-start mb-1">
                                    <div>
                                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold text-white ${getEventColor(event.type)}`}>
                                            {event.type.replace('_', ' ').toUpperCase()}
                                        </span>
                                        <span className="ml-2 text-xs text-gray-500">
                                            {new Date(event.timestamp * 1000).toISOString().substr(11, 8)}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <div className="w-16 bg-gray-200 rounded-full h-2">
                                            <div
                                                className={`h-2 rounded-full ${getEventColor(event.type)}`}
                                                style={{ width: `${event.importance * 100}%` }}
                                            />
                                        </div>
                                        <span className="text-xs text-gray-500">{(event.importance * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                                <p className="text-sm text-gray-700">{event.description}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
