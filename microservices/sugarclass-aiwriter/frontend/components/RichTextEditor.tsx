'use client'

import { useCallback, useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'
import TextAlign from '@tiptap/extension-text-align'
import TextStyle from '@tiptap/extension-text-style'
import Color from '@tiptap/extension-color'
import FontFamily from '@tiptap/extension-font-family'
import { Highlight } from '@tiptap/extension-highlight'
import {
    Bold,
    Italic,
    Underline as UnderlineIcon,
    Strikethrough,
    Heading1,
    Heading2,
    Heading3,
    List,
    ListOrdered,
    AlignLeft,
    AlignCenter,
    AlignRight,
    Link as LinkIcon,
    Unlink,
    Type,
    Highlighter,
    Undo,
    Redo
} from 'lucide-react'

interface SelectionInfo {
    text: string
    from: number
    to: number
}

export interface RichTextEditorRef {
    replaceSelection: (text: string, from: number, to: number) => void
}

interface RichTextEditorProps {
    content: string
    contentJson?: string
    onChange: (content: string, html: string, json: string) => void
    placeholder?: string
    className?: string
    onSelectionChange?: (selection: SelectionInfo) => void  // Callback for selection changes
}

const fontFamilies = [
    { name: 'Sans Serif', value: 'sans-serif' },
    { name: 'Serif', value: 'serif' },
    { name: 'Monospace', value: 'monospace' },
    { name: 'Arial', value: 'Arial, sans-serif' },
    { name: 'Georgia', value: 'Georgia, serif' },
    { name: 'Times New Roman', value: '"Times New Roman", serif' },
    { name: 'Courier New', value: '"Courier New", monospace' },
    { name: 'Verdana', value: 'Verdana, sans-serif' },
]

const textColors = [
    { name: 'Black', value: '#000000' },
    { name: 'Red', value: '#ef4444' },
    { name: 'Orange', value: '#f97316' },
    { name: 'Yellow', value: '#eab308' },
    { name: 'Green', value: '#22c55e' },
    { name: 'Blue', value: '#3b82f6' },
    { name: 'Purple', value: '#a855f7' },
    { name: 'Gray', value: '#6b7280' },
]

const highlightColors = [
    { name: 'None', value: 'transparent' },
    { name: 'Yellow', value: '#fef08a' },
    { name: 'Green', value: '#bbf7d0' },
    { name: 'Blue', value: '#bfdbfe' },
    { name: 'Pink', value: '#fbcfe8' },
    { name: 'Orange', value: '#fed7aa' },
]

const RichTextEditor = forwardRef<RichTextEditorRef, RichTextEditorProps>(function RichTextEditor({
    content,
    contentJson,
    onChange,
    placeholder = 'Start writing...',
    className = '',
    onSelectionChange
}: RichTextEditorProps, ref) {
    // Color dropdown states
    const [textColorOpen, setTextColorOpen] = useState(false)
    const [highlightColorOpen, setHighlightColorOpen] = useState(false)
    const textColorRef = useRef<HTMLDivElement>(null)
    const highlightColorRef = useRef<HTMLDivElement>(null)

    // Initialize editor first - must be before any useEffect that uses it
    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                heading: {
                    levels: [1, 2, 3, 4, 5, 6],
                },
            }),
            Underline,
            Link.configure({
                openOnClick: false,
                HTMLAttributes: {
                    class: 'text-primary underline hover:text-accent',
                },
            }),
            TextAlign.configure({
                types: ['heading', 'paragraph'],
            }),
            TextStyle,
            Color.configure({
                types: ['textStyle'],
            }),
            FontFamily.configure({
                types: ['textStyle'],
            }),
            Highlight.configure({
                multicolor: true,
            }),
        ],
        editorProps: {
            attributes: {
                class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-xl focus:outline-none max-w-none min-h-[500px] p-4 text-text-primary [&_ul]:list-disc [&_ul]:ml-4 [&_ol]:list-decimal [&_ol]:ml-4 [&_li]:my-1',
            },
        },
        onUpdate: ({ editor }) => {
            const html = editor.getHTML()
            const json = JSON.stringify(editor.getJSON())
            const text = editor.getText()
            onChange(text, html, json)
        },
        onCreate: ({ editor }) => {
            // Use JSON content if available (preserves all formatting)
            // Otherwise fall back to plain text content
            if (contentJson) {
                try {
                    editor.commands.setContent(JSON.parse(contentJson), false)
                } catch {
                    // If JSON is invalid, fall back to plain text
                    editor.commands.setContent(content || '', false)
                }
            } else {
                editor.commands.setContent(content || '', false)
            }
            // Initialize with current content
            if (content || contentJson) {
                onChange(editor.getText(), editor.getHTML(), JSON.stringify(editor.getJSON()))
            }
        },
    })

    // Expose methods via ref
    useImperativeHandle(ref, () => ({
        replaceSelection: (text: string, from: number, to: number) => {
            if (!editor) return
            // Delete the selected range and insert the new text
            editor.view.dispatch(
                editor.view.state.tr
                    .delete(from, to)
                    .insertText(text, from)
            )
            // Trigger content update
            onChange(editor.getText(), editor.getHTML(), JSON.stringify(editor.getJSON()))
        }
    }), [editor, onChange])

    // Close dropdowns when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (textColorRef.current && !textColorRef.current.contains(event.target as Node)) {
                setTextColorOpen(false)
            }
            if (highlightColorRef.current && !highlightColorRef.current.contains(event.target as Node)) {
                setHighlightColorOpen(false)
            }
        }

        document.addEventListener('mousedown', handleClickOutside)
        return () => {
            document.removeEventListener('mousedown', handleClickOutside)
        }
    }, [])

    // Track text selection and notify parent
    useEffect(() => {
        if (!editor || !onSelectionChange) return

        const handleSelectionUpdate = () => {
            const { from, to } = editor.state.selection
            // Only report non-empty selections
            if (from !== to) {
                const selectedText = editor.state.doc.textBetween(from, to, ' ')
                onSelectionChange({ text: selectedText, from, to })
            }
        }

        editor.on('selectionUpdate', handleSelectionUpdate)
        editor.on('transaction', handleSelectionUpdate)

        return () => {
            editor.off('selectionUpdate', handleSelectionUpdate)
            editor.off('transaction', handleSelectionUpdate)
        }
    }, [editor, onSelectionChange])

    // Update editor content when prop changes
    useEffect(() => {
        if (!editor) return

        const currentText = editor.getText()

        // If JSON content is provided, use it (preserves all formatting)
        if (contentJson) {
            try {
                const jsonDoc = JSON.parse(contentJson)
                const currentJson = editor.getJSON()
                // Only update if significantly different
                if (JSON.stringify(jsonDoc) !== JSON.stringify(currentJson)) {
                    editor.commands.setContent(jsonDoc, false)
                }
            } catch {
                // If JSON is invalid, fall back to text comparison
                if (currentText === '' || Math.abs(currentText.length - content.length) > 10) {
                    editor.commands.setContent(content || '', false)
                }
            }
        } else if (content !== currentText) {
            // Only update if significantly different to avoid cursor jumps
            if (currentText === '' || Math.abs(currentText.length - content.length) > 10) {
                editor.commands.setContent(content || '', false)
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [content, contentJson])

    const setLink = useCallback(() => {
        if (!editor) return

        const previousUrl = editor.getAttributes('link').href
        const url = window.prompt('Enter URL:', previousUrl)

        // cancelled
        if (url === null) {
            return
        }

        // empty
        if (url === '') {
            editor.chain().focus().extendMarkRange('link').unsetLink().run()
            return
        }

        // update link
        editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
    }, [editor])

    if (!editor) {
        return (
            <div className="w-full h-[500px] p-4 border border-border rounded-lg bg-surface animate-pulse">
                <div className="h-4 bg-surface-dark rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-surface-dark rounded w-1/2 mb-2"></div>
                <div className="h-4 bg-surface-dark rounded w-5/6"></div>
            </div>
        )
    }

    return (
        <div className={`border border-border rounded-lg bg-surface overflow-hidden ${className}`}>
            {/* Toolbar */}
            <div className="border-b border-border bg-surface-dark/30 p-2 flex flex-wrap gap-1">
                {/* Undo/Redo */}
                <div className="flex gap-1 border-r border-border pr-2 mr-2">
                    <button
                        onClick={() => editor.chain().focus().undo().run()}
                        disabled={!editor.can().undo()}
                        className="p-2 rounded hover:bg-surface-dark disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        title="Undo"
                    >
                        <Undo className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => editor.chain().focus().redo().run()}
                        disabled={!editor.can().redo()}
                        className="p-2 rounded hover:bg-surface-dark disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        title="Redo"
                    >
                        <Redo className="w-4 h-4" />
                    </button>
                </div>

                {/* Basic Formatting */}
                <div className="flex gap-1 border-r border-border pr-2 mr-2">
                    <button
                        onClick={() => editor.chain().focus().toggleBold().run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('bold') ? 'bg-primary/20 text-primary' : ''}`}
                        title="Bold"
                    >
                        <Bold className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => editor.chain().focus().toggleItalic().run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('italic') ? 'bg-primary/20 text-primary' : ''}`}
                        title="Italic"
                    >
                        <Italic className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => editor.chain().focus().toggleUnderline().run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('underline') ? 'bg-primary/20 text-primary' : ''}`}
                        title="Underline"
                    >
                        <UnderlineIcon className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => editor.chain().focus().toggleStrike().run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('strike') ? 'bg-primary/20 text-primary' : ''}`}
                        title="Strikethrough"
                    >
                        <Strikethrough className="w-4 h-4" />
                    </button>
                </div>

                {/* Headings */}
                <div className="flex gap-1 border-r border-border pr-2 mr-2">
                    <button
                        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('heading', { level: 1 }) ? 'bg-primary/20 text-primary' : ''}`}
                        title="Heading 1"
                    >
                        <Heading1 className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('heading', { level: 2 }) ? 'bg-primary/20 text-primary' : ''}`}
                        title="Heading 2"
                    >
                        <Heading2 className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('heading', { level: 3 }) ? 'bg-primary/20 text-primary' : ''}`}
                        title="Heading 3"
                    >
                        <Heading3 className="w-4 h-4" />
                    </button>
                </div>

                {/* Lists */}
                <div className="flex gap-1 border-r border-border pr-2 mr-2">
                    <button
                        onMouseDown={(e) => {
                            e.preventDefault()
                            editor.commands.toggleBulletList()
                        }}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('bulletList') ? 'bg-primary/20 text-primary' : ''}`}
                        title="Bullet List"
                    >
                        <List className="w-4 h-4" />
                    </button>
                    <button
                        onMouseDown={(e) => {
                            e.preventDefault()
                            editor.commands.toggleOrderedList()
                        }}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('orderedList') ? 'bg-primary/20 text-primary' : ''}`}
                        title="Numbered List"
                    >
                        <ListOrdered className="w-4 h-4" />
                    </button>
                </div>

                {/* Alignment */}
                <div className="flex gap-1 border-r border-border pr-2 mr-2">
                    <button
                        onClick={() => editor.chain().focus().setTextAlign('left').run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive({ textAlign: 'left' }) ? 'bg-primary/20 text-primary' : ''}`}
                        title="Align Left"
                    >
                        <AlignLeft className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => editor.chain().focus().setTextAlign('center').run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive({ textAlign: 'center' }) ? 'bg-primary/20 text-primary' : ''}`}
                        title="Align Center"
                    >
                        <AlignCenter className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => editor.chain().focus().setTextAlign('right').run()}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive({ textAlign: 'right' }) ? 'bg-primary/20 text-primary' : ''}`}
                        title="Align Right"
                    >
                        <AlignRight className="w-4 h-4" />
                    </button>
                </div>

                {/* Font Family */}
                <div className="flex gap-1 border-r border-border pr-2 mr-2 items-center">
                    <Type className="w-4 h-4 text-text-muted" />
                    <select
                        value={(editor.getAttributes('textStyle') as any).fontFamily || (editor.getAttributes('fontFamily') as any).fontFamily || 'sans-serif'}
                        onChange={(e) => {
                            editor.chain().focus().setFontFamily(e.target.value).run()
                        }}
                        className="bg-surface border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                        title="Font Family"
                    >
                        {fontFamilies.map(font => (
                            <option key={font.value} value={font.value}>
                                {font.name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Text Color */}
                <div className="flex gap-1 border-r border-border pr-2 mr-2 items-center" ref={textColorRef}>
                    <div className="relative">
                        <button
                            onClick={() => setTextColorOpen(!textColorOpen)}
                            className={`p-2 rounded transition-colors ${textColorOpen ? 'bg-surface-dark' : 'hover:bg-surface-dark'}`}
                            title="Text Color"
                        >
                            <div className="w-4 h-4 rounded" style={{ backgroundColor: (editor.getAttributes('textStyle') as any).color || '#000000' }} />
                        </button>
                        {textColorOpen && (
                            <div className="absolute top-full left-0 mt-1 bg-surface border border-border rounded-lg shadow-lg p-2 flex flex-col gap-1 z-10">
                                {textColors.map(color => (
                                    <button
                                        key={color.value}
                                        onMouseDown={(e) => {
                                            e.preventDefault()
                                            editor.chain().focus().setColor(color.value).run()
                                            setTextColorOpen(false)
                                        }}
                                        className="w-6 h-6 rounded border border-border hover:scale-110 transition-transform"
                                        style={{ backgroundColor: color.value }}
                                        title={color.name}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Highlight Color */}
                <div className="flex gap-1 border-r border-border pr-2 mr-2 items-center" ref={highlightColorRef}>
                    <div className="relative">
                        <button
                            onClick={() => setHighlightColorOpen(!highlightColorOpen)}
                            className={`p-2 rounded transition-colors ${highlightColorOpen ? 'bg-surface-dark' : 'hover:bg-surface-dark'}`}
                            title="Highlight"
                        >
                            <Highlighter className="w-4 h-4" />
                        </button>
                        {highlightColorOpen && (
                            <div className="absolute top-full left-0 mt-1 bg-surface border border-border rounded-lg shadow-lg p-2 flex flex-col gap-1 z-10">
                                {highlightColors.map(color => (
                                    <button
                                        key={color.value}
                                        onMouseDown={(e) => {
                                            e.preventDefault()
                                            if (color.value === 'transparent') {
                                                editor.chain().focus().unsetHighlight().run()
                                            } else {
                                                editor.chain().focus().setHighlight({ color: color.value }).run()
                                            }
                                            setHighlightColorOpen(false)
                                        }}
                                        className="w-6 h-6 rounded border border-border hover:scale-110 transition-transform"
                                        style={{ backgroundColor: color.value }}
                                        title={color.name}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Link */}
                <div className="flex gap-1">
                    <button
                        onClick={setLink}
                        className={`p-2 rounded hover:bg-surface-dark transition-colors ${editor.isActive('link') ? 'bg-primary/20 text-primary' : ''}`}
                        title="Add Link"
                    >
                        <LinkIcon className="w-4 h-4" />
                    </button>
                    {editor.isActive('link') && (
                        <button
                            onClick={() => editor.chain().focus().unsetLink().run()}
                            className="p-2 rounded hover:bg-surface-dark transition-colors"
                            title="Remove Link"
                        >
                            <Unlink className="w-4 h-4" />
                        </button>
                    )}
                </div>
            </div>

            {/* Editor Content */}
            <EditorContent editor={editor} placeholder={placeholder} />

            {/* Character Count */}
            <div className="border-t border-border bg-surface-dark/30 px-4 py-2 text-xs text-text-muted text-right">
                {editor.storage.characterCount?.characters() || editor.getText().length} characters
            </div>
        </div>
    )
})

export default RichTextEditor
