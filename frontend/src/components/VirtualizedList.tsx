import { memo, useMemo, useState, useEffect, useRef } from 'react';

interface VirtualizedListItem {
  id: string;
  height: number;
  content: React.ReactNode;
}

interface VirtualizedListProps {
  items: VirtualizedListItem[];
  containerHeight: number;
  itemHeight: number;
  overscan?: number;
}

export const VirtualizedList: React.FC<VirtualizedListProps> = memo(({
  items,
  containerHeight,
  itemHeight,
  overscan = 5
}) => {
  const [scrollTop, setScrollTop] = useState(0);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  const visibleRange = useMemo(() => {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(
      startIndex + Math.ceil(containerHeight / itemHeight),
      items.length - 1
    );

    return {
      start: Math.max(0, startIndex - overscan),
      end: Math.min(items.length - 1, endIndex + overscan)
    };
  }, [scrollTop, containerHeight, itemHeight, items.length, overscan]);

  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end + 1);
  }, [items, visibleRange]);

  const totalHeight = items.length * itemHeight;
  const offsetY = visibleRange.start * itemHeight;

  useEffect(() => {
    // Auto-scroll to bottom when new items are added
    if (scrollElementRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollElementRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      
      if (isAtBottom) {
        scrollElementRef.current.scrollTop = scrollHeight;
      }
    }
  }, [items.length]);

  return (
    <div
      ref={scrollElementRef}
      style={{
        height: containerHeight,
        overflowY: 'auto',
        position: 'relative'
      }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ 
          transform: `translateY(${offsetY}px)`,
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0
        }}>
          {visibleItems.map((item, index) => (
            <div
              key={item.id}
              style={{
                height: itemHeight,
                overflow: 'hidden'
              }}
            >
              {item.content}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});