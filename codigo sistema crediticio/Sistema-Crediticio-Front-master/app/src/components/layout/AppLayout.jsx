import { NavLink } from 'react-router-dom'
import {
  IconLayoutDashboard,
  IconUpload,
  IconSearch,
  IconActivity,
} from '@tabler/icons-react'
import { NAV_ITEMS } from '../../config/constants.js'

const ICONS = {
  LayoutDashboard: IconLayoutDashboard,
  Upload: IconUpload,
  Search: IconSearch,
  Activity: IconActivity,
}

export function AppLayout({ children }) {
  return (
    <div className="min-h-screen flex bg-(--color-bg)">
      {/* Sidebar */}
      <aside className="w-[240px] bg-(--color-navy) flex flex-col sticky top-0 h-screen flex-shrink-0">
        <div className="px-6 pt-6 pb-5 border-b border-white/10">
          <img
            src="/LogoV1.png"
            alt="Colsubsidio"
            className="h-8 w-auto brightness-0 invert"
          />
          <p className="mt-3 text-[10px] font-semibold text-white/50 uppercase tracking-[0.12em]">
            Motor de Ofertas
          </p>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = ICONS[item.icon]
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-white/15 text-white'
                      : 'text-white/60 hover:text-white hover:bg-white/8'
                  }`
                }
              >
                <Icon size={18} strokeWidth={1.5} />
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        <div className="px-4 py-4 border-t border-white/10">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-white/15 flex items-center justify-center">
              <span className="text-xs font-semibold text-white/80">AN</span>
            </div>
            <div className="text-xs">
              <p className="font-medium text-white/80">Analista</p>
              <p className="text-white/40">Demo</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <main className="flex-1 page-container">{children}</main>
      </div>
    </div>
  )
}
