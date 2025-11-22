"use client";

import React, { useState, useEffect } from 'react';

interface Face {
    face_id: string;
    timestamp: number;
    person_name: string | null;
    cluster_id: number | null;
}

interface FaceGalleryProps {
    videoId: string | null;
}

export default function FaceGallery({ videoId }: FaceGalleryProps) {
    const [clusters, setClusters] = useState<Record<number, Face[]>>({});
    const [loading, setLoading] = useState(false);
    const [tagging, setTagging] = useState<string | null>(null);
    const [personName, setPersonName] = useState('');

    useEffect(() => {
        if (videoId) {
            loadFaceClusters();
        }
    }, [videoId]);

    const loadFaceClusters = async () => {
        if (!videoId) return;

        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/api/faces/clusters?video_id=${videoId}`);
            const data = await response.json();
            setClusters(data.clusters);
        } catch (error) {
            console.error('Error loading face clusters:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleTagFace = async (faceId: string) => {
        if (!personName.trim()) {
            alert('Please enter a person name');
            return;
        }

        try {
            await fetch(`http://localhost:8000/api/faces/tag?face_id=${faceId}&person_name=${encodeURIComponent(personName)}`, {
                method: 'POST'
            });
            setTagging(null);
            setPersonName('');
            loadFaceClusters(); // Reload to show updated tags
        } catch (error) {
            console.error('Error tagging face:', error);
        }
    };

    if (!videoId) {
        return null;
    }

    if (loading) {
        return <div className="text-center py-4">Loading faces...</div>;
    }

    const clusterEntries = Object.entries(clusters).filter(([id]) => id !== '-1'); // Exclude noise

    if (clusterEntries.length === 0) {
        return <div className="text-center py-4 text-gray-500">No faces detected in this video</div>;
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-xl font-semibold mb-4">Detected Faces</h2>
            <p className="text-sm text-gray-600 mb-4">
                Faces are automatically grouped by person. Click to tag them with names.
            </p>

            <div className="space-y-6">
                {clusterEntries.map(([clusterId, faces]) => (
                    <div key={clusterId} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-3">
                            <h3 className="font-semibold text-gray-700">
                                {faces[0].person_name || `Person ${parseInt(clusterId) + 1}`}
                            </h3>
                            <span className="text-sm text-gray-500">{faces.length} appearances</span>
                        </div>

                        <div className="flex gap-2 flex-wrap mb-3">
                            {faces.slice(0, 5).map((face) => (
                                <div key={face.face_id} className="text-xs bg-blue-50 px-2 py-1 rounded">
                                    {new Date(face.timestamp * 1000).toISOString().substr(11, 8)}
                                </div>
                            ))}
                            {faces.length > 5 && (
                                <div className="text-xs text-gray-500 px-2 py-1">
                                    +{faces.length - 5} more
                                </div>
                            )}
                        </div>

                        {!faces[0].person_name && (
                            <div>
                                {tagging === clusterId ? (
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            value={personName}
                                            onChange={(e) => setPersonName(e.target.value)}
                                            placeholder="Enter person name"
                                            className="flex-1 px-3 py-1 border border-gray-300 rounded text-sm"
                                            onKeyDown={(e) => e.key === 'Enter' && handleTagFace(faces[0].face_id)}
                                        />
                                        <button
                                            onClick={() => handleTagFace(faces[0].face_id)}
                                            className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                                        >
                                            Save
                                        </button>
                                        <button
                                            onClick={() => { setTagging(null); setPersonName(''); }}
                                            className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm hover:bg-gray-400"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => setTagging(clusterId)}
                                        className="px-4 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                                    >
                                        Tag Person
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
