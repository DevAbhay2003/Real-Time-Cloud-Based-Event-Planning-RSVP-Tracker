import { useState, useEffect, useRef } from 'react';

export function useEventRealtime(eventId) {
  const [counts, setCounts] = useState({
    going: 0,
    maybe: 0,
    not_going: 0,
    maximum_capacity: 0,
    available_seats: 0,
    waitlist_count: 0,
    status: 'PUBLISHED'
  });
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!eventId) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = import.meta.env.VITE_WS_URL || `${wsProtocol}//127.0.0.1:8000`;
    const wsUrl = `${wsHost}/ws/events/${eventId}`;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'INITIAL_STATE' || data.type === 'RSVP_UPDATED') {
          setCounts(data.counts);
        }
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
    };

    socket.onerror = (err) => {
      console.error('WebSocket connection error:', err);
      setIsConnected(false);
    };

    // Ping interval to keep connection alive
    const pingInterval = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send('ping');
      }
    }, 25000);

    return () => {
      clearInterval(pingInterval);
      socket.close();
    };
  }, [eventId]);

  return { counts, isConnected };
}
