export function HiveMark({ compact = false }: { compact?: boolean }) {
  return (
    <span className={compact ? "hive-mark hive-mark--compact" : "hive-mark"} aria-label="Hive Coder">
      <svg viewBox="0 0 48 48" aria-hidden="true" focusable="false">
        <path d="M24 3.8 41.4 13.9v20.2L24 44.2 6.6 34.1V13.9L24 3.8Z" className="hive-mark__frame" />
        <path d="M16 15.5v17M32 15.5v17M16 24h16" className="hive-mark__glyph" />
        <circle cx="24" cy="24" r="2.8" className="hive-mark__core" />
      </svg>
    </span>
  );
}
