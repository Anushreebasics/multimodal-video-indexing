"use client";

import React, { useState, useRef } from 'react';
import VideoPlayer from '@/components/VideoPlayer';
import SearchResults from '@/components/SearchResults';
import FaceGallery from '@/components/FaceGallery';
import EntityViewer from '@/components/EntityViewer';
import EventTimeline from '@/components/EventTimeline';

export default function Home() {
    const [videoFile, setVideoFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [videoId, setVideoId] = useState<string | null>(null);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [currentTimestamp, setCurrentTimestamp] = useState<number | null>(null);
    const [qaMode, setQaMode] = useState(false);
    const [qaAnswer, setQaAnswer] = useState<any>(null);
    const [qaLoading, setQaLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'search' | 'qa' | 'faces' | 'entities' | 'timeline'>('search');
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setVideoFile(e.target.files[0]);
        }
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setVideoFile(e.dataTransfer.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!videoFile) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', videoFile);

        try {
            const response = await fetch('http://localhost:8000/api/upload', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            setVideoId(data.video_id);
            setVideoUrl(`http://localhost:8000/uploads/${data.filename}`);
        } catch (error) {
            console.error('Error uploading file:', error);
            alert('Error uploading file');
        } finally {
            setUploading(false);
        }
    };

    const handleSearch = async () => {
        if (!searchQuery) return;

        try {
            const url = videoId
                ? `http://localhost:8000/api/search?query=${encodeURIComponent(searchQuery)}&video_id=${videoId}`
                : `http://localhost:8000/api/search?query=${encodeURIComponent(searchQuery)}`;
            const response = await fetch(url);
            const data = await response.json();
            setSearchResults(data.results.slice(0, 1));
        } catch (error) {
            console.error('Error searching:', error);
        }
    };

    const handleAskQuestion = async () => {
        if (!searchQuery || !videoId) {
            alert('Please upload a video first and enter a question.');
            return;
        }

        setQaLoading(true);
        setQaAnswer(null);

        try {
            const url = `http://localhost:8000/api/qa?question=${encodeURIComponent(searchQuery)}&video_id=${videoId}`;
            const response = await fetch(url, { method: 'POST' });
            const data = await response.json();

            setQaAnswer(data);
            if (data.timestamp !== undefined) {
                setCurrentTimestamp(data.timestamp);
            }
        } catch (error) {
            console.error('Error asking question:', error);
            setQaAnswer({ error: 'Failed to get answer' });
        } finally {
            setQaLoading(false);
        }
    };

    return (
        <main className="min-h-screen relative overflow-hidden">
            {/* Background Glow Effects */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-500/20 rounded-full blur-[120px] -z-10" />
            <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-purple-500/10 rounded-full blur-[100px] -z-10" />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Hero Section */}
                <div className="text-center mb-16 animate-fade-in">
                    <div className="inline-block mb-4 px-4 py-1.5 rounded-full glass border border-white/10 text-sm font-medium text-blue-300">
                        ✨ Next-Gen Video Intelligence
                    </div>
                    <h1 className="text-6xl font-bold mb-6 tracking-tight">
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 animate-pulse-slow">
                            Multimodal Video Indexer
                        </span>
                    </h1>
                    <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
                        Unlock the power of your video content with AI-driven semantic search,
                        face recognition, and knowledge graph extraction.
                    </p>
                </div>

                {/* Upload Section */}
                <div className="mb-12 animate-slide-up">
                    <div
                        className={`relative glass-card rounded-2xl p-8 transition-all duration-300 ${dragActive ? 'border-blue-500 bg-blue-500/10' : 'hover:border-white/20'}`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                    >
                        <div className="flex flex-col items-center justify-center text-center">
                            <div className="w-16 h-16 mb-4 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400">
                                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">
                                {videoFile ? videoFile.name : "Upload Video"}
                            </h3>
                            <p className="text-gray-400 mb-6">
                                {videoFile ? "Ready to process" : "Drag & drop or click to browse"}
                            </p>

                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="video/*"
                                onChange={handleFileChange}
                                className="hidden"
                            />

                            <div className="flex gap-4">
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="px-6 py-2.5 rounded-lg glass hover:bg-white/10 transition-colors text-white font-medium"
                                >
                                    Select File
                                </button>
                                <button
                                    onClick={handleUpload}
                                    disabled={!videoFile || uploading}
                                    className={`px-8 py-2.5 rounded-lg font-medium transition-all shadow-lg shadow-blue-500/25 ${!videoFile || uploading
                                            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                            : 'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white'
                                        }`}
                                >
                                    {uploading ? 'Processing...' : 'Start Analysis'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-slide-up" style={{ animationDelay: '0.2s' }}>
                    {/* Left: Video Player */}
                    <div className="lg:col-span-2 space-y-6">
                        {videoUrl ? (
                            <div className="glass-card p-1 rounded-2xl overflow-hidden">
                                <div className="bg-black/50 rounded-xl overflow-hidden">
                                    <VideoPlayer src={videoUrl} timestamp={currentTimestamp} />
                                </div>
                            </div>
                        ) : (
                            <div className="glass-card rounded-2xl aspect-video flex items-center justify-center text-gray-500">
                                <div className="text-center">
                                    <p className="text-lg font-medium mb-2">No Video Loaded</p>
                                    <p className="text-sm opacity-60">Upload a video to see the player</p>
                                </div>
                            </div>
                        )}

                        {/* Feature Info Cards */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="glass p-4 rounded-xl border-l-4 border-blue-500">
                                <h4 className="font-semibold text-blue-400 text-sm mb-1">Semantic Search</h4>
                                <p className="text-xs text-gray-400">Find moments by description</p>
                            </div>
                            <div className="glass p-4 rounded-xl border-l-4 border-purple-500">
                                <h4 className="font-semibold text-purple-400 text-sm mb-1">AI QA</h4>
                                <p className="text-xs text-gray-400">Ask questions about content</p>
                            </div>
                            <div className="glass p-4 rounded-xl border-l-4 border-green-500">
                                <h4 className="font-semibold text-green-400 text-sm mb-1">Knowledge Graph</h4>
                                <p className="text-xs text-gray-400">Entity linking & relationships</p>
                            </div>
                        </div>
                    </div>

                    {/* Right: Feature Tabs */}
                    <div className="lg:col-span-1">
                        <div className="glass-card rounded-2xl overflow-hidden h-full flex flex-col">
                            {/* Tab Headers */}
                            <div className="flex overflow-x-auto p-2 gap-1 border-b border-white/5 scrollbar-hide">
                                {['search', 'qa', 'faces', 'entities', 'timeline'].map((tab) => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab as any)}
                                        className={`flex-1 py-2.5 px-3 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${activeTab === tab
                                                ? 'bg-white/10 text-white shadow-sm'
                                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                                            }`}
                                    >
                                        {tab === 'search' && '🔍 Search'}
                                        {tab === 'qa' && '💬 Ask AI'}
                                        {tab === 'faces' && '👤 Faces'}
                                        {tab === 'entities' && '🧠 Entities'}
                                        {tab === 'timeline' && '⏱️ Events'}
                                    </button>
                                ))}
                            </div>

                            {/* Tab Content */}
                            <div className="p-6 flex-1 overflow-y-auto max-h-[600px]">
                                {/* Search Tab */}
                                {activeTab === 'search' && (
                                    <div className="space-y-6 animate-fade-in">
                                        <div>
                                            <h3 className="text-lg font-semibold text-white mb-2">Semantic Search</h3>
                                            <p className="text-sm text-gray-400">
                                                Search for objects, actions, or text within the video.
                                            </p>
                                        </div>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                placeholder="e.g., person running..."
                                                className="flex-1 glass-input rounded-lg px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder-gray-500"
                                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                            />
                                            <button
                                                onClick={handleSearch}
                                                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
                                            >
                                                Search
                                            </button>
                                        </div>
                                        <SearchResults
                                            results={searchResults}
                                            onResultClick={(timestamp) => setCurrentTimestamp(timestamp)}
                                        />
                                    </div>
                                )}

                                {/* QA Tab */}
                                {activeTab === 'qa' && (
                                    <div className="space-y-6 animate-fade-in">
                                        <div>
                                            <h3 className="text-lg font-semibold text-white mb-2">Video QA</h3>
                                            <p className="text-sm text-gray-400">
                                                Ask natural language questions about the video.
                                            </p>
                                        </div>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                placeholder="What is the person holding?"
                                                className="flex-1 glass-input rounded-lg px-4 py-2.5 outline-none focus:ring-2 focus:ring-purple-500/50 transition-all placeholder-gray-500"
                                                onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
                                            />
                                            <button
                                                onClick={handleAskQuestion}
                                                disabled={qaLoading}
                                                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors disabled:opacity-50"
                                            >
                                                {qaLoading ? '...' : 'Ask'}
                                            </button>
                                        </div>
                                        {qaAnswer && (
                                            <div className="glass p-4 rounded-xl border border-purple-500/30">
                                                {qaAnswer.error ? (
                                                    <p className="text-red-400">{qaAnswer.error}</p>
                                                ) : (
                                                    <p className="text-gray-200 font-medium">{qaAnswer.answer}</p>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Faces Tab */}
                                {activeTab === 'faces' && (
                                    <div className="space-y-6 animate-fade-in">
                                        <div>
                                            <h3 className="text-lg font-semibold text-white mb-2">Detected Faces</h3>
                                            <p className="text-sm text-gray-400">
                                                Identified individuals in the video.
                                            </p>
                                        </div>
                                        {videoId ? (
                                            <FaceGallery videoId={videoId} />
                                        ) : (
                                            <div className="text-center py-12 text-gray-500">
                                                Upload a video to detect faces
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Entities Tab */}
                                {activeTab === 'entities' && (
                                    <div className="space-y-6 animate-fade-in">
                                        <div>
                                            <h3 className="text-lg font-semibold text-white mb-2">Knowledge Graph</h3>
                                            <p className="text-sm text-gray-400">
                                                Connected entities and concepts.
                                            </p>
                                        </div>
                                        <EntityViewer videoId={videoId} />
                                    </div>
                                )}

                                {/* Timeline Tab */}
                                {activeTab === 'timeline' && (
                                    <div className="space-y-6 animate-fade-in">
                                        <div>
                                            <h3 className="text-lg font-semibold text-white mb-2">Event Timeline</h3>
                                            <p className="text-sm text-gray-400">
                                                Key moments and scene changes.
                                            </p>
                                        </div>
                                        <EventTimeline videoId={videoId} onSeek={(timestamp) => setCurrentTimestamp(timestamp)} />
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
