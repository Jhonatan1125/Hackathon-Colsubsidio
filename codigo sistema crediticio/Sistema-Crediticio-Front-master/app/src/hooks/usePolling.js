import { useEffect, useRef, useState, useCallback } from 'react'

/**
 * Hook to poll a callback while a condition is met.
 * @param {() => Promise<T>} fetchFn - async function to call
 * @param {boolean} active - whether polling should be active
 * @param {number} interval - polling interval in ms
 * @param {(data: T) => boolean} shouldStop - returns true when polling should stop
 */
export function usePolling(fetchFn, active, interval, shouldStop = () => false) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)
  const fetchFnRef = useRef(fetchFn)
  const shouldStopRef = useRef(shouldStop)

  useEffect(() => {
    fetchFnRef.current = fetchFn
  }, [fetchFn])

  useEffect(() => {
    shouldStopRef.current = shouldStop
  }, [shouldStop])

  useEffect(() => {
    if (!active) {
      clearInterval(intervalRef.current)
      return
    }

    let cancelled = false

    const call = async () => {
      setLoading(true)
      try {
        const result = await fetchFnRef.current()
        if (cancelled) return
        setData(result)
        setError(null)
        if (shouldStopRef.current(result)) {
          clearInterval(intervalRef.current)
        }
      } catch (err) {
        if (cancelled) return
        setError(err?.message || 'Error desconocido')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    call()
    intervalRef.current = setInterval(call, interval)

    return () => {
      cancelled = true
      clearInterval(intervalRef.current)
    }
  }, [active, interval])

  return { data, loading, error }
}
