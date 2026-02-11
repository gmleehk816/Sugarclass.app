// ===========================================================================
// Chunk Parser — Robust HTML ↔ Chunks Conversion
// ===========================================================================

export type ChunkType = 'text' | 'heading' | 'image' | 'video' | 'list' | 'quote' | 'callout' | 'table';

export interface ContentChunk {
    id: string;
    type: ChunkType;
    content: string;
}

let chunkCounter = 0;
const nextId = (): string => {
    chunkCounter++;
    return `ck_${Date.now().toString(36)}_${chunkCounter}`;
};

// Block-level tags that should NOT be unwrapped (they are leaf-level chunks)
const LEAF_BLOCK_TAGS = new Set([
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'table', 'blockquote', 'pre',
    'figure', 'iframe', 'img', 'hr', 'details',
]);

// Container tags that should be recursively unwrapped
const CONTAINER_TAGS = new Set(['div', 'section', 'article', 'main', 'aside', 'header', 'footer', 'nav']);

// Tags that are inline (not block-level)
const INLINE_TAGS = new Set([
    'span', 'a', 'strong', 'b', 'em', 'i', 'u', 's', 'del',
    'mark', 'small', 'sub', 'sup', 'code', 'abbr', 'cite',
    'br', 'wbr', 'time', 'data', 'var', 'kbd', 'samp',
]);

/**
 * Classify an HTML element into a ChunkType.
 */
function classifyElement(el: Element): ChunkType {
    const tag = el.tagName.toLowerCase();

    if (/^h[1-6]$/.test(tag)) return 'heading';
    if (tag === 'ul' || tag === 'ol') return 'list';
    if (tag === 'blockquote') return 'quote';
    if (tag === 'details') return 'callout';
    if (tag === 'table') return 'table';
    if (tag === 'figure') {
        if (el.querySelector('img')) return 'image';
        if (el.querySelector('iframe') || el.querySelector('video')) return 'video';
        return 'text';
    }
    if (tag === 'img') return 'image';
    if (tag === 'iframe' || tag === 'video') return 'video';

    // Check if a div/section/etc wraps a single media element
    if (CONTAINER_TAGS.has(tag)) {
        const inner = el.querySelector('img, iframe, video');
        if (inner && el.children.length <= 2) {
            if (inner.tagName === 'IMG') return 'image';
            return 'video';
        }
    }

    return 'text';
}

/**
 * Check if a node is inline-level (text node or inline element).
 */
function isInlineNode(node: Node): boolean {
    if (node.nodeType === Node.TEXT_NODE) return true;
    if (node.nodeType === Node.ELEMENT_NODE) {
        const tag = (node as Element).tagName.toLowerCase();
        return INLINE_TAGS.has(tag);
    }
    return false;
}

/**
 * Check if an element is a "container" that should be recursively unwrapped.
 * A container is unwrapped when it has multiple block-level children.
 */
function shouldUnwrap(el: Element): boolean {
    const tag = el.tagName.toLowerCase();
    if (!CONTAINER_TAGS.has(tag)) return false;

    // Count block-level children
    let blockChildCount = 0;
    for (const child of Array.from(el.childNodes)) {
        if (child.nodeType === Node.ELEMENT_NODE) {
            const childTag = (child as Element).tagName.toLowerCase();
            if (!INLINE_TAGS.has(childTag)) {
                blockChildCount++;
            }
        }
    }

    return blockChildCount > 1;
}

/**
 * Recursively extract chunks from a DOM node.
 */
function extractChunks(node: Node, chunks: ContentChunk[]): void {
    if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent?.trim();
        if (text) {
            chunks.push({ id: nextId(), type: 'text', content: `<p>${text}</p>` });
        }
        return;
    }

    if (node.nodeType !== Node.ELEMENT_NODE) return;

    const el = node as Element;
    const tag = el.tagName.toLowerCase();

    // Skip empty elements
    if (!el.innerHTML.trim() && tag !== 'hr' && tag !== 'br' && tag !== 'img' && tag !== 'iframe') {
        return;
    }

    // If it's a container with multiple block children, unwrap it
    if (shouldUnwrap(el)) {
        // Flush any consecutive inline children as a merged text chunk
        let inlineBuffer: string[] = [];

        const flushInlines = () => {
            if (inlineBuffer.length > 0) {
                const merged = inlineBuffer.join('').trim();
                if (merged) {
                    chunks.push({ id: nextId(), type: 'text', content: `<p>${merged}</p>` });
                }
                inlineBuffer = [];
            }
        };

        for (const child of Array.from(el.childNodes)) {
            if (isInlineNode(child)) {
                if (child.nodeType === Node.TEXT_NODE) {
                    const text = child.textContent || '';
                    if (text.trim()) inlineBuffer.push(text);
                } else {
                    inlineBuffer.push((child as Element).outerHTML);
                }
            } else {
                flushInlines();
                extractChunks(child, chunks);
            }
        }
        flushInlines();
        return;
    }

    // It's a leaf-level block or a container with only inline/single-block content
    const type = classifyElement(el);
    chunks.push({ id: nextId(), type, content: el.outerHTML });
}

/**
 * Parse an HTML string into an array of ContentChunks.
 * Uses DOMParser for reliable HTML parsing and recursive unwrapping.
 */
export function parseHtmlToChunks(html: string): ContentChunk[] {
    if (typeof window === 'undefined') return [];
    if (!html || !html.trim()) return [];

    // Reset counter for deterministic IDs within a parse call
    chunkCounter = 0;

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const chunks: ContentChunk[] = [];

    for (const child of Array.from(doc.body.childNodes)) {
        extractChunks(child, chunks);
    }

    // Fallback: if parsing produced nothing but HTML exists, create one text chunk
    if (chunks.length === 0 && html.trim()) {
        chunks.push({ id: nextId(), type: 'text', content: html });
    }

    return chunks;
}

/**
 * Re-assemble ContentChunks back into a single HTML string.
 * Separates chunks with newlines for readability.
 */
export function chunksToHtml(chunks: ContentChunk[]): string {
    return chunks.map(c => c.content).join('\n');
}
