"use client";

import React from 'react';

interface SearchResult {
    id: string;
    text: string;
    metadata: {
        type: string;
        timestamp?: number;
        start?: number;
        end?: number;
        video_id: string;
        objects?: string;
    };
    distance: number;
}

interface SearchResultsProps {
    results: SearchResult[];
    onResultClick: (timestamp: number) => void;
}

const SearchResults: React.FC<SearchResultsProps> = ({ results, onResultClick }) => {
    if (results.length === 0) {
        return <div className="text-gray-500 mt-4">No results found.</div>;
    }

    return (
        <div className="mt-6 space-y-4">
            <h3 className="text-xl font-semibold text-gray-800">Search Results</h3>
            <div className="grid gap-4">
                {results.map((result) => {
                    const timestamp = result.metadata.timestamp || result.metadata.start || 0;
                    const type = result.metadata.type;

                    return (
                        <div
                            key={result.id}
                            onClick={() => onResultClick(timestamp)}
                            className="glass p-4 rounded-lg hover:bg-white/10 transition-all cursor-pointer border border-white/10"
                        >
                            <div className="flex justify-between items-start">
                                <div>
                                    <span className={`inline-block px-2 py-1 text-xs font-semibold rounded-full mb-2 ${type === 'transcript' ? 'bg-blue-500/20 text-blue-300' :
                                        type === 'visual' ? 'bg-green-500/20 text-green-300' :
                                            'bg-purple-500/20 text-purple-300'
                                        }`}>
                                        {type.toUpperCase()}
                                    </span>
                                    <p className="text-gray-200 font-medium">{result.text}</p>
                                    <p className="text-sm text-gray-400 mt-1">
                                        Time: {new Date(timestamp * 1000).toISOString().substr(11, 8)}
                                    </p>
                                </div>
                                <div className="text-xs text-gray-500">
                                    Score: {result.distance.toFixed(4)}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default SearchResults;
