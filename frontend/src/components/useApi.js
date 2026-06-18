import { useEffect, useState, useCallback } from 'react'

// Generic data hook. `fn` should be stable (wrap in useCallback at call site
// if it depends on props).
export function useApi(fn, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(() => {
    setLoading(true)
    fn()
      .then((d) => { setData(d); setError(null) })
      .catch((e) => setError(e))
      .finally(() => setLoading(false))
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { reload() }, [reload])
  return { data, error, loading, reload, setData }
}
