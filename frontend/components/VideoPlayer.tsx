"use client";

import React, { useRef, useEffect } from 'react';

interface VideoPlayerProps {
    src: string;
    timestamp: number | null;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ src, timestamp }) => {
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        if (videoRef.current && timestamp !== null) {
            videoRef.current.currentTime = timestamp;
            videoRef.current.play();
        }
    }, [timestamp, src]);

    return (
        <div className="w-full max-w-4xl mx-auto bg-black rounded-lg overflow-hidden shadow-xl">
            <video
                ref={videoRef}
                src={src}
                controls
                className="w-full h-auto"
            />
        </div>
    );
};

export default VideoPlayer;
