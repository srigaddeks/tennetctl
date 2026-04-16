"use client"
import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function ControlTestsRedirect() {
  const router = useRouter()
  useEffect(() => { router.replace("/admin/control-test-library") }, [router])
  return null
}
