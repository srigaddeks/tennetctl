"use client"

import * as React from "react"
import { 
  Settings,
  Bell,
  User,
  Shield,
  Palette,
  Save,
  Loader2,
  CheckCircle2,
  Lock,
  Globe,
  Fingerprint
} from "lucide-react"

import { 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Badge,
  Input,
  Switch
} from "@kcontrol/ui"
import { toast } from "sonner"

interface SettingsSection {
  id: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
}

interface SettingsViewProps {
  orgId?: string
}

export function SettingsView({ 
  orgId
}: SettingsViewProps) {
  const [isSaving, setIsSaving] = React.useState(false)
  const [settings, setSettings] = React.useState({
    notifications: {
      email: true,
      push: true,
      evidenceRequests: true,
      taskUpdates: true,
      messages: true
    },
    display: {
      darkMode: true,
      compactView: false,
      showBadges: true
    },
    privacy: {
      shareActivity: false,
      allowAnalytics: true
    }
  })

  // Settings sections
  const settingsSections: SettingsSection[] = [
    {
      id: 'notifications',
      title: 'Alert Protocols',
      description: 'Configure real-time intelligence & notification channels',
      icon: Bell
    },
    {
      id: 'display',
      title: 'Visual Interface',
      description: 'Customize the auditor workspace aesthetics & density',
      icon: Palette
    },
    {
      id: 'privacy',
      title: 'Security & Privacy',
      description: 'Manage data isolation and activity tracking parameters',
      icon: Shield
    }
  ]

  // Handle save settings
  const handleSaveSettings = async () => {
    setIsSaving(true)
    const promise = new Promise(resolve => setTimeout(resolve, 1500))
    
    toast.promise(promise, {
      loading: 'Syncing preferences to cloud...',
      success: () => {
        setIsSaving(false)
        return 'Settings synchronized successfully.'
      },
      error: () => {
        setIsSaving(false)
        return 'Failed to synchronize settings.'
      }
    })
  }

  // Handle toggle setting
  const handleToggleSetting = (sectionId: string, key: string) => {
    setSettings(prev => {
        const anyPrev = prev as any
        return {
            ...prev,
            [sectionId]: {
                ...anyPrev[sectionId],
                [key]: !anyPrev[sectionId][key]
            }
        }
    })
  }

  return (
    <div className="max-w-4xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-6">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-white/90">PORTAL PREFERENCES</h2>
          <p className="text-sm text-teal-400/60 font-medium uppercase tracking-widest mt-1">
            Global auditor workspace configuration & security policy
          </p>
        </div>
        <Button 
          onClick={handleSaveSettings}
          disabled={isSaving}
          className="rounded-full h-11 px-8 font-extrabold uppercase tracking-widest gap-2 bg-primary text-primary-foreground hover:scale-105 active:scale-95 transition-all shadow-[0_0_20px_rgba(var(--primary),0.3)]"
        >
          {isSaving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          Apply Changes
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Sidebar Nav */}
        <div className="space-y-2">
            {settingsSections.map(section => (
                <button
                    key={section.id}
                    className="w-full flex items-center gap-4 p-4 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10 transition-all text-left group"
                >
                    <div className="h-10 w-10 rounded-xl bg-black/20 flex items-center justify-center text-white/40 group-hover:text-primary transition-colors">
                        <section.icon className="h-5 w-5" />
                    </div>
                    <div>
                        <p className="text-xs font-black text-white/80 uppercase tracking-tight">{section.title}</p>
                        <p className="text-[10px] text-white/20 font-bold uppercase tracking-widest truncate max-w-[120px]">Active</p>
                    </div>
                </button>
            ))}
        </div>

        {/* Content Area */}
        <div className="md:col-span-2 space-y-6">
            {settingsSections.map(section => (
                <Card key={section.id} className="bg-black/40 border-white/10 shadow-2xl backdrop-blur-xl overflow-hidden glass-container">
                    <CardHeader className="bg-white/5 border-b border-white/5">
                        <div className="flex items-center gap-4">
                             <div className="h-10 w-10 rounded-xl bg-teal-500/10 flex items-center justify-center text-teal-500">
                                <section.icon className="h-5 w-5" />
                             </div>
                             <div>
                                <CardTitle className="text-sm font-black uppercase tracking-tight text-white/90">{section.title}</CardTitle>
                                <p className="text-[10px] text-white/30 font-bold uppercase tracking-[0.1em]">{section.description}</p>
                             </div>
                        </div>
                    </CardHeader>
                    <CardContent className="p-6 space-y-4">
                        {section.id === 'notifications' && Object.entries(settings.notifications).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                                <div>
                                    <p className="text-sm font-bold text-white/80 uppercase tracking-tight capitalize">{key.replace(/([A-Z])/g, ' $1')}</p>
                                    <p className="text-[10px] font-bold text-white/20 uppercase tracking-widest mt-0.5">Toggle channel delivery</p>
                                </div>
                                <Switch
                                    isSelected={value}
                                    onChange={() => handleToggleSetting('notifications', key)}
                                />
                            </div>
                        ))}
                         {section.id === 'display' && Object.entries(settings.display).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                                <div>
                                    <p className="text-sm font-bold text-white/80 uppercase tracking-tight capitalize">{key.replace(/([A-Z])/g, ' $1')}</p>
                                    <p className="text-[10px] font-bold text-white/20 uppercase tracking-widest mt-0.5">UI rendering preference</p>
                                </div>
                                <Switch
                                    isSelected={value}
                                    onChange={() => handleToggleSetting('display', key)}
                                />
                            </div>
                        ))}
                        {section.id === 'privacy' && Object.entries(settings.privacy).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                                <div>
                                    <p className="text-sm font-bold text-white/80 uppercase tracking-tight capitalize">{key.replace(/([A-Z])/g, ' $1')}</p>
                                    <p className="text-[10px] font-bold text-white/20 uppercase tracking-widest mt-0.5">Global policy enforcement</p>
                                </div>
                                <Switch
                                    isSelected={value}
                                    onChange={() => handleToggleSetting('privacy', key)}
                                />
                            </div>
                        ))}
                    </CardContent>
                </Card>
            ))}

            {/* Account Info */}
            <Card className="bg-black/80 border-teal-500/20 shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden">
                <CardHeader className="bg-teal-500/5 border-b border-teal-500/10">
                    <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-xl bg-teal-500/20 flex items-center justify-center text-teal-400">
                            <Fingerprint className="h-5 w-5" />
                        </div>
                        <div>
                            <CardTitle className="text-sm font-black uppercase tracking-tight text-teal-400">Auditor Identity</CardTitle>
                            <p className="text-[10px] text-teal-400/40 font-bold uppercase tracking-widest">Signed Evidence Signature: <span className="font-mono text-teal-400/60">#AUD-992-X</span></p>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="p-6 space-y-6">
                    <div className="grid grid-cols-2 gap-8">
                        <div>
                            <p className="text-[10px] font-black text-white/20 uppercase tracking-[0.2em] mb-2">Verified Identity</p>
                            <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded-full bg-white/5 flex items-center justify-center text-xs font-bold text-white/60">A</div>
                                <p className="text-sm font-black text-white/80 tracking-tight">auditor@kreesalis.com</p>
                            </div>
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-white/20 uppercase tracking-[0.2em] mb-2">Security Clearance</p>
                            <Badge className="bg-teal-500/10 text-teal-400 border-teal-500/20 font-black uppercase tracking-widest text-[10px]">Level 4 (Audit Partner)</Badge>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
      </div>
      
      <style jsx global>{`
        .glass-container {
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-container:hover {
            transform: translateY(-2px);
            border-color: rgba(20, 184, 166, 0.2);
        }
      `}</style>
    </div>
  )
}
