import React, { useState, useEffect, useRef } from 'react';
import { FiPlay, FiPause, FiSquare, FiRefreshCw } from 'react-icons/fi';
import { MorsePlayer } from '../utils/morseLogic';

const MorseAudioControls = ({ morseCode }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [volume, setVolume] = useState(0.5);
    const [speed, setSpeed] = useState(1.0);
    const playerRef = useRef(null);

    useEffect(() => {
        playerRef.current = new MorsePlayer();
        return () => {
            if (playerRef.current) playerRef.current.stop();
        };
    }, []);

    const handlePlay = () => {
        if (!playerRef.current || !morseCode) return;
        
        if (isPaused) {
            playerRef.current.resume();
            setIsPaused(false);
            setIsPlaying(true);
        } else {
            playerRef.current.setVolume(volume);
            playerRef.current.setPlaybackSpeed(speed);
            playerRef.current.play(morseCode, () => {
                setIsPlaying(false);
                setIsPaused(false);
            });
            setIsPlaying(true);
            setIsPaused(false);
        }
    };

    const handlePause = () => {
        if (playerRef.current && isPlaying) {
            playerRef.current.pause();
            setIsPaused(true);
            setIsPlaying(false);
        }
    };

    const handleStop = () => {
        if (playerRef.current) {
            playerRef.current.stop();
            setIsPlaying(false);
            setIsPaused(false);
        }
    };

    const handleReplay = () => {
        handleStop();
        setTimeout(handlePlay, 50);
    };

    const handleVolumeChange = (e) => {
        const val = parseFloat(e.target.value);
        setVolume(val);
        if (playerRef.current) playerRef.current.setVolume(val);
    };

    const handleSpeedChange = (e) => {
        const val = parseFloat(e.target.value);
        setSpeed(val);
        if (playerRef.current) playerRef.current.setPlaybackSpeed(val);
    };

    return (
        <div className="flex flex-col gap-4 bg-surface/40 p-4 rounded-lg border border-white/10 shadow-inner mt-4 w-full">
            <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-primary tracking-wider">AUDIO CONTROLS</span>
                <div className="flex gap-2">
                    {!isPlaying && !isPaused && (
                        <button onClick={handlePlay} className="p-2 bg-primary/20 hover:bg-primary/40 text-primary rounded-full transition-colors" title="Play">
                            <FiPlay />
                        </button>
                    )}
                    {isPlaying && (
                        <button onClick={handlePause} className="p-2 bg-yellow-500/20 hover:bg-yellow-500/40 text-yellow-500 rounded-full transition-colors" title="Pause">
                            <FiPause />
                        </button>
                    )}
                    {isPaused && (
                        <button onClick={handlePlay} className="p-2 bg-primary/20 hover:bg-primary/40 text-primary rounded-full transition-colors" title="Resume">
                            <FiPlay />
                        </button>
                    )}
                    <button onClick={handleStop} disabled={!isPlaying && !isPaused} className={`p-2 rounded-full transition-colors ${isPlaying || isPaused ? 'bg-danger/20 hover:bg-danger/40 text-danger' : 'bg-surface text-text-muted cursor-not-allowed'}`} title="Stop">
                        <FiSquare />
                    </button>
                    <button onClick={handleReplay} className="p-2 bg-accent/20 hover:bg-accent/40 text-accent rounded-full transition-colors" title="Replay">
                        <FiRefreshCw />
                    </button>
                </div>
            </div>
            
            <div className="grid grid-cols-2 gap-6">
                <div className="flex flex-col">
                    <label className="text-xs text-text-muted mb-2 flex justify-between">
                        <span>Speed</span>
                        <span>{speed}x</span>
                    </label>
                    <input type="range" min="0.5" max="3" step="0.25" value={speed} onChange={handleSpeedChange} className="accent-primary" />
                </div>
                <div className="flex flex-col">
                    <label className="text-xs text-text-muted mb-2 flex justify-between">
                        <span>Volume</span>
                        <span>{Math.round(volume * 100)}%</span>
                    </label>
                    <input type="range" min="0" max="1" step="0.05" value={volume} onChange={handleVolumeChange} className="accent-primary" />
                </div>
            </div>
        </div>
    );
};

export default MorseAudioControls;
