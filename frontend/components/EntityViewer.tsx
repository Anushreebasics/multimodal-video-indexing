"use client";

import React, { useState, useEffect } from 'react';

interface Entity {
    text: string;
    label: string;
    timestamp: number;
    wikidata?: {
        wikidata_id: string;
        label: string;
        description: string;
        url: string;
    };
}

interface EntityViewerProps {
    videoId: string | null;
}

export default function EntityViewer({ videoId }: EntityViewerProps) {
    const [entities, setEntities] = useState<Entity[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedType, setSelectedType] = useState<string>('all');

    useEffect(() => {
        if (videoId) {
            loadEntities();
        }
    }, [videoId]);

    const loadEntities = async () => {
        if (!videoId) return;

        setLoading(true);
        try {
            // Search for entities in the video
            const response = await fetch(`http://localhost:8000/api/search?query=&video_id=${videoId}`);
            const data = await response.json();

            console.log('Search results:', data.results);

            // Filter for entity type results
            const entityResults = data.results.filter((r: any) => r.metadata?.type === 'entity');
            console.log('Entity results:', entityResults);

            // Extract entity name from the text (format: "EntityName (TYPE)")
            const extractedEntities = entityResults.map((r: any) => {
                const text = r.text || '';
                // Extract entity name from "EntityName (TYPE) - description" format
                const match = text.match(/^(.+?)\s*\(/);
                const entityName = match ? match[1].trim() : text;

                return {
                    text: entityName,
                    label: r.metadata?.entity_type || 'UNKNOWN',
                    timestamp: r.metadata?.timestamp || 0,
                    wikidata: r.metadata?.wikidata_id ? {
                        wikidata_id: r.metadata.wikidata_id,
                        label: entityName,
                        description: '',
                        url: `https://www.wikidata.org/wiki/${r.metadata.wikidata_id}`
                    } : undefined
                };
            });

            console.log('Extracted entities:', extractedEntities);
            setEntities(extractedEntities);
        } catch (error) {
            console.error('Error loading entities:', error);
        } finally {
            setLoading(false);
        }
    };

    if (!videoId) {
        return <p className="text-gray-500 text-center py-8">Upload a video to see extracted entities</p>;
    }

    if (loading) {
        return <div className="text-center py-4">Loading entities...</div>;
    }

    const entityTypes = ['all', ...new Set(entities.map(e => e.label))];
    const filteredEntities = selectedType === 'all'
        ? entities
        : entities.filter(e => e.label === selectedType);

    if (entities.length === 0) {
        return <p className="text-gray-500 text-center py-8">No entities detected in this video</p>;
    }

    return (
        <div className="space-y-4">
            {/* Entity Type Filter */}
            <div className="flex gap-2 flex-wrap">
                {entityTypes.map(type => (
                    <button
                        key={type}
                        onClick={() => setSelectedType(type)}
                        className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${selectedType === type
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        {type.toUpperCase()}
                    </button>
                ))}
            </div>

            {/* Entity List */}
            <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredEntities.map((entity, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors">
                        <div className="flex justify-between items-start mb-1">
                            <div className="flex-1">
                                <div className="flex items-center gap-2">
                                    <span className="font-semibold text-gray-900">{entity.text}</span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${entity.label === 'PERSON' ? 'bg-blue-100 text-blue-800' :
                                        entity.label === 'GPE' ? 'bg-green-100 text-green-800' :
                                            entity.label === 'ORG' ? 'bg-purple-100 text-purple-800' :
                                                'bg-gray-100 text-gray-800'
                                        }`}>
                                        {entity.label}
                                    </span>
                                </div>
                                {entity.wikidata && (
                                    <a
                                        href={entity.wikidata.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs text-blue-600 hover:underline flex items-center gap-1 mt-1"
                                    >
                                        🔗 {entity.wikidata.wikidata_id}
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                        </svg>
                                    </a>
                                )}
                            </div>
                            <span className="text-xs text-gray-500">
                                {new Date(entity.timestamp * 1000).toISOString().substr(11, 8)}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
