"use client";

import React, { useState } from 'react';
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

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setVideoFile(e.target.files[0]);
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
            console.log('Upload response:', data);
            setVideoId(data.video_id);
            console.log('Video ID set to:', data.video_id);
            // Assuming backend serves uploads at /uploads
            setVideoUrl(`http://localhost:8000/uploads/${data.filename}`);
            alert('Upload successful! Processing started.');
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
            // Only search within the current video if one is loaded
            const url = videoId
                ? `http://localhost:8000/api/search?query=${encodeURIComponent(searchQuery)}&video_id=${videoId}`
                : `http://localhost:8000/api/search?query=${encodeURIComponent(searchQuery)}`;
            const response = await fetch(url);
            const data = await response.json();
            setSearchResults(data.results);
        } catch (error) {
            console.error('Error searching:', error);
        }
    };

    const handleAskQuestion = async () => {
        if (!searchQuery || !videoId) {
            alert('Please upload a video first and enter a question.');
            return;
        }

        console.log('Asking question:', searchQuery, 'for video:', videoId);
        setQaLoading(true);
        setQaAnswer(null);

        try {
            const url = `http://localhost:8000/api/qa?question=${encodeURIComponent(searchQuery)}&video_id=${videoId}`;
            console.log('Fetching:', url);

            const response = await fetch(url, { method: 'POST' });
            console.log('Response status:', response.status);

            const data = await response.json();
            console.log('Response data:', data);

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
        <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
                        Multimodal Intelligent Video Indexing
                    </h1>
                    <p className="text-lg text-gray-600">
                        Advanced AI-powered video analysis with semantic search, face recognition, and knowledge graphs
                    </p>
                </div>

                {/* Upload Section */}
                <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-200 mb-6">
                    <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                        <span className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm">1</span>
                        Upload Video
                    </h2>
                    <div className="flex gap-4">
                        <input
                            type="file"
                            accept="video/*"
                            onChange={handleFileChange}
                            className="block w-full text-sm text-gray-500
                                file:mr-4 file:py-3 file:px-6
                                file:rounded-full file:border-0
                                file:text-sm file:font-semibold
                                file:bg-blue-50 file:text-blue-700
                                hover:file:bg-blue-100 cursor-pointer"
                        />
                        <button
                            onClick={handleUpload}
                            disabled={!videoFile || uploading}
                            className={`px-8 py-3 rounded-full font-semibold text-white transition-all shadow-md ${!videoFile || uploading
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg'
                                }`}
                        >
                            {uploading ? 'Uploading...' : 'Upload'}
                        </button>
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left: Video Player */}
                    <div className="lg:col-span-2">
                        {videoUrl && (
                            <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-200">
                                <h2 className="text-xl font-semibold mb-4">Video Player</h2>
                                <VideoPlayer src={videoUrl} timestamp={currentTimestamp} />
                            </div>
                        )}
                    </div>

                    {/* Right: Feature Tabs */}
                    <div className="lg:col-span-1">
                        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
                            {/* Tab Headers */}
                            <div className="flex border-b border-gray-200">
                                <button
                                    onClick={() => setActiveTab('search')}
                                    className={`flex-1 py-4 px-3 font-semibold transition-colors text-sm ${activeTab === 'search'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                                        }`}
                                >
                                    🔍 Search
                                </button>
                                <button
                                    onClick={() => setActiveTab('qa')}
                                    className={`flex-1 py-4 px-3 font-semibold transition-colors text-sm ${activeTab === 'qa'
                                        ? 'bg-purple-600 text-white'
                                        : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                                        }`}
                                >
                                    💬 Ask AI
                                </button>
                                <button
                                    onClick={() => setActiveTab('faces')}
                                    className={`flex-1 py-4 px-3 font-semibold transition-colors text-sm ${activeTab === 'faces'
                                        ? 'bg-green-600 text-white'
                                        : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                                        }`}
                                >
                                    👤 Faces
                                </button>
                                <button
                                    onClick={() => setActiveTab('entities')}
                                    className={`flex-1 py-4 px-3 font-semibold transition-colors text-sm ${activeTab === 'entities'
                                        ? 'bg-orange-600 text-white'
                                        : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                                        }`}
                                >
                                    🧠 Entities
                                </button>
                                <button
                                    onClick={() => setActiveTab('timeline')}
                                    className={`flex-1 py-4 px-3 font-semibold transition-colors text-sm ${activeTab === 'timeline'
                                        ? 'bg-indigo-600 text-white'
                                        : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                                        }`}
                                >
                                    ⏱️ Events
                                </button>
                            </div>

                            {/* Tab Content */}
                            <div className="p-6">
                                {/* Search Tab */}
                                {activeTab === 'search' && (
                                    <div className="space-y-4">
                                        <h3 className="text-lg font-semibold text-gray-900">Semantic Search</h3>
                                        <p className="text-sm text-gray-600">
                                            Search for objects, speech, text, or entities using natural language
                                        </p>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                placeholder="e.g., person running, red car, Paris..."
                                                className="flex-1 rounded-lg border-gray-300 border px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                            />
                                            <button
                                                onClick={handleSearch}
                                                className="px-6 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors shadow-md"
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
                                    <div className="space-y-4">
                                        <h3 className="text-lg font-semibold text-gray-900">Video Question Answering</h3>
                                        <p className="text-sm text-gray-600">
                                            Ask questions about the video content using BLIP-2
                                        </p>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                placeholder="What color is the car?"
                                                className="flex-1 rounded-lg border-gray-300 border px-4 py-2 focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                                                onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
                                            />
                                            <button
                                                onClick={handleAskQuestion}
                                                disabled={qaLoading}
                                                className={`px-6 py-2 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors shadow-md ${qaLoading ? 'opacity-50 cursor-not-allowed' : ''
                                                    }`}
                                            >
                                                {qaLoading ? '...' : 'Ask'}
                                            </button>
                                        </div>
                                        {qaAnswer && (
                                            <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-4 rounded-lg border border-purple-200">
                                                {qaAnswer.error ? (
                                                    <p className="text-red-600">{qaAnswer.error}</p>
                                                ) : (
                                                    <>
                                                        <p className="text-gray-800 font-medium mb-2">{qaAnswer.answer}</p>
                                                        {/* <div className="text-xs text-gray-600">
                                                            <p><strong>Q:</strong> {qaAnswer.question}</p>
                                                            <p><strong>Time:</strong> {new Date(qaAnswer.timestamp * 1000).toISOString().substr(11, 8)}</p>
                                                        </div> */}
                                                    </>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Faces Tab */}
                                {activeTab === 'faces' && (
                                    <div className="space-y-4">
                                        <h3 className="text-lg font-semibold text-gray-900">Face Recognition</h3>
                                        <p className="text-sm text-gray-600">
                                            View and tag detected faces in the video
                                        </p>
                                        {videoId ? (
                                            <FaceGallery videoId={videoId} />
                                        ) : (
                                            <p className="text-gray-500 text-center py-8">Upload a video to detect faces</p>
                                        )}
                                    </div>
                                )}

                                {/* Entities Tab */}
                                {activeTab === 'entities' && (
                                    <div className="space-y-4">
                                        <h3 className="text-lg font-semibold text-gray-900">Knowledge Graph</h3>
                                        <p className="text-sm text-gray-600">
                                            Named entities linked to Wikidata
                                        </p>
                                        <EntityViewer videoId={videoId} />
                                    </div>
                                )}

                                {/* Timeline Tab */}
                                {activeTab === 'timeline' && (
                                    <div className="space-y-4">
                                        <h3 className="text-lg font-semibold text-gray-900">Event Timeline</h3>
                                        <p className="text-sm text-gray-600">
                                            Automatically detected highlights and scene changes
                                        </p>
                                        <EventTimeline videoId={videoId} onSeek={(timestamp) => setCurrentTimestamp(timestamp)} />
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Feature Info Cards */}
                        <div className="mt-6 grid grid-cols-1 gap-3">
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                <h4 className="font-semibold text-blue-900 text-sm mb-1">🎯 Multimodal Search</h4>
                                <p className="text-xs text-blue-700">Speech, objects, OCR, faces, and entities</p>
                            </div>
                            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                                <h4 className="font-semibold text-purple-900 text-sm mb-1">🤖 AI-Powered QA</h4>
                                <p className="text-xs text-purple-700">BLIP-2 visual question answering</p>
                            </div>
                            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                                <h4 className="font-semibold text-green-900 text-sm mb-1">🧠 Knowledge Graph</h4>
                                <p className="text-xs text-green-700">Entity linking with Wikidata</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
