# REACT & FRAMER SKILL

## CP Template
```tsx
"use client";
import { type FC, useState, useCallback } from "react";
import { motion, type Variants } from "framer-motion";
import { cn } from "@/lib/utils";

interface Props {
  className?: string;
  variant?: "primary" | "secondary";
}

const variants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export const ComponentName: FC<Props> = ({ className, variant = "primary" }) => {
  const [st, setSt] = useState<Type>(initial);
  const handler = useCallback((arg: Type) => {
    setSt(prev => /* transform */);
  }, [deps]);

  return (
    <motion.div
      className={cn("base-classes", className)}
      variants={variants} initial="hidden" animate="visible"
    >
      {/* JSX */}
    </motion.div>
  );
};
```

## Animation Patterns

### Page Transition
```tsx
const pageVariants: Variants = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
};
```

### Stagger Children
```tsx
const container: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};
const item: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 },
};
```

### Hover/Tap
```tsx
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  transition={{ type: "spring", stiffness: 400 }}
/>
```

## File Structure
```
src/
├── components/{ui,layout,features}/
├── hooks/
├── lib/
├── types/
└── app/
```

## Anti-Patterns [NEVER DO]
- ❌ Inline styles except for dynamic VALs
- ❌ `useEffect` for derived ST (use `useMemo`)
- ❌ PROP drilling >3 levels (use CTX)
- ❌ Animating `height`/`width` (use `scale`/`layout`)
- ❌ Missing `key` in mapped lists
- ❌ `any` type — use `unknown` + type guard
