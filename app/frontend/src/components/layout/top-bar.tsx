import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useTranslation } from '@/i18n/I18nProvider';
import { PanelBottom, PanelLeft, PanelRight, Settings, Languages } from 'lucide-react';

interface TopBarProps {
  isLeftCollapsed: boolean;
  isRightCollapsed: boolean;
  isBottomCollapsed: boolean;
  onToggleLeft: () => void;
  onToggleRight: () => void;
  onToggleBottom: () => void;
  onSettingsClick: () => void;
}

export function TopBar({
  isLeftCollapsed,
  isRightCollapsed,
  isBottomCollapsed,
  onToggleLeft,
  onToggleRight,
  onToggleBottom,
  onSettingsClick,
}: TopBarProps) {
  const { t, toggleLanguage, locale } = useTranslation();

  return (
    <div className="absolute top-0 right-0 z-40 flex items-center gap-0 py-1 px-2 bg-panel/80">
      {/* Language Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={toggleLanguage}
        className="h-8 px-2 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors text-xs gap-1"
        title={locale === 'zh' ? 'Switch to English' : '切换到中文'}
      >
        <Languages size={14} />
        <span>{locale === 'zh' ? 'EN' : '中'}</span>
      </Button>

      {/* Left Sidebar Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggleLeft}
        className={cn(
          "h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors",
          !isLeftCollapsed && "text-foreground"
        )}
        aria-label={t('Toggle left sidebar')}
        title={t('Toggle left sidebar') + ' (⌘B)'}
      >
        <PanelLeft size={16} />
      </Button>

      {/* Bottom Panel Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggleBottom}
        className={cn(
          "h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors",
          !isBottomCollapsed && "text-foreground"
        )}
        aria-label={t('Toggle bottom panel')}
        title={t('Toggle bottom panel') + ' (⌘J)'}
      >
        <PanelBottom size={16} />
      </Button>

      {/* Right Sidebar Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggleRight}
        className={cn(
          "h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors",
          !isRightCollapsed && "text-foreground"
        )}
        aria-label={t('Toggle right sidebar')}
        title={t('Toggle right sidebar') + ' (⌘I)'}
      >
        <PanelRight size={16} />
      </Button>

      {/* Divider */}
      <div className="w-px h-5 bg-ramp-grey-700 mx-1" />

      {/* Settings */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onSettingsClick}
        className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors"
        aria-label={t('Open settings')}
        title={t('Open settings') + ' (⌘,)'}
      >
        <Settings size={16} />
      </Button>
    </div>
  );
}
