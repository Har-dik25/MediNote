import { useState, useRef, useEffect } from 'react';

export default function AudioRecorder({ onRecordingComplete }) {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState('');
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const canvasRef = useRef(null);
  
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const sourceRef = useRef(null);

  useEffect(() => {
    return () => {
      stopRecording();
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, []);

  async function startRecording() {
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const type = mediaRecorder.mimeType || 'audio/webm';
        const blob = new Blob(audioChunksRef.current, { type });
        // Create a fake File object to match the previous upload behavior
        const file = new File([blob], 'recording.wav', { type: blob.type, lastModified: Date.now() });
        onRecordingComplete(file);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      
      setupVisualizer(stream);
    } catch (err) {
      setError('Could not access microphone. Please allow permissions in your browser.');
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  }

  function setupVisualizer(stream) {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    // Create Analyser
    analyserRef.current = audioContextRef.current.createAnalyser();
    analyserRef.current.fftSize = 256;
    
    // Connect stream to analyser
    sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
    sourceRef.current.connect(analyserRef.current);
    
    drawWaveform();
  }

  function drawWaveform() {
    if (!canvasRef.current || !analyserRef.current) return;
    
    const canvas = canvasRef.current;
    const canvasCtx = canvas.getContext('2d');
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    analyserRef.current.getByteTimeDomainData(dataArray);
    
    // Clear canvas
    canvasCtx.fillStyle = 'var(--paper)';
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
    
    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = 'var(--teal)';
    canvasCtx.beginPath();
    
    const sliceWidth = canvas.width * 1.0 / bufferLength;
    let x = 0;
    
    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = v * canvas.height / 2;
      
      if (i === 0) {
        canvasCtx.moveTo(x, y);
      } else {
        canvasCtx.lineTo(x, y);
      }
      x += sliceWidth;
    }
    
    canvasCtx.lineTo(canvas.width, canvas.height / 2);
    canvasCtx.stroke();
    
    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(drawWaveform);
    }
  }

  return (
    <div style={{ textAlign: 'center', padding: '16px 0' }}>
      {error && <p className="field-error" style={{ marginBottom: 12 }}>{error}</p>}
      
      <div style={{ position: 'relative', width: '100%', height: 60, background: 'var(--paper)', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--rule)', marginBottom: 16 }}>
        {!isRecording ? (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-faint)', fontSize: '0.85rem' }}>
            Ready to record
          </div>
        ) : (
          <canvas ref={canvasRef} width={400} height={60} style={{ width: '100%', height: '100%' }} />
        )}
      </div>

      {!isRecording ? (
        <button type="button" className="btn-primary" style={{ background: 'var(--alert)' }} onClick={startRecording}>
          <span style={{ fontSize: 16, marginRight: 6 }}>●</span> Start Recording
        </button>
      ) : (
        <button type="button" className="btn-outline" onClick={stopRecording}>
          <span style={{ fontSize: 16, marginRight: 6, color: 'var(--alert)' }}>■</span> Stop Recording
        </button>
      )}
    </div>
  );
}
