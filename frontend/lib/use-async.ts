"use client"

import { useCallback, useEffect, useRef, useState } from "react"

import { ApiError } from "./api"

export interface AsyncState<T> {
  data: T | null
  error: ApiError | null
  loading: boolean
  reload: () => void
  setData: (updater: T | null | ((prev: T | null) => T | null)) => void
}

/**
 * Run an async loader whenever `deps` change. Ignores results from stale runs
 * so fast filter changes can't display out-of-order data.
 */
export function useAsync<T>(loader: () => Promise<T>, deps: React.DependencyList): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [loading, setLoading] = useState(true)
  const [tick, setTick] = useState(0)
  const runId = useRef(0)
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  useEffect(() => {
    const id = ++runId.current
    setLoading(true)
    setError(null)
    loaderRef
      .current()
      .then((result) => {
        if (runId.current !== id) return
        setData(result)
        setLoading(false)
      })
      .catch((err: unknown) => {
        if (runId.current !== id) return
        setError(err instanceof ApiError ? err : new ApiError(0, "Something went wrong."))
        setLoading(false)
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])

  return { data, error, loading, reload, setData }
}

export function errorMessage(err: unknown, fallback = "Something went wrong. Please try again."): string {
  return err instanceof ApiError ? err.message : fallback
}
