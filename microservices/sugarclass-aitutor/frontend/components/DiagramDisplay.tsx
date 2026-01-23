import React from 'react';
import { DocumentImage } from '../types';

interface DiagramDisplayProps {
    diagram?: string;
    documentImages?: DocumentImage[];
}

const DiagramDisplay: React.FC<DiagramDisplayProps> = ({ diagram, documentImages }) => {
    if (!diagram && (!documentImages || documentImages.length === 0)) {
        return null;
    }

    const getMimeType = (base64: string): string => {
        if (!base64 || typeof base64 !== 'string') return 'image/png';
        if (base64.startsWith('/9j/')) return 'image/jpeg';
        if (base64.startsWith('iVBOR')) return 'image/png';
        if (base64.startsWith('R0lGOD')) return 'image/gif';
        return 'image/png';
    };

    return (
        <div className="mt-4 space-y-4">
            {/* Generated Diagram */}
            {diagram && (
                <div className="rounded-lg overflow-hidden border-2 border-orange-500/20 bg-orange-500/5 p-4">
                    <div className="text-xs font-bold text-gray-600 uppercase tracking-widest mb-2">
                        📊 Generated Visualization
                    </div>
                    <img
                        src={`data:image/png;base64,${diagram}`}
                        alt="Generated Diagram"
                        className="w-full rounded-lg shadow-md"
                    />
                </div>
            )}

            {/* Document Images */}
            {documentImages && documentImages.length > 0 && (
                <div>
                    <div className="text-xs font-bold text-gray-600 uppercase tracking-widest mb-3">
                        📸 Related Images
                    </div>
                    <div className="space-y-4">
                        {documentImages.map((img, idx) => {
                            const caption = img.caption || img.description || `Image ${idx + 1}`;
                            const mimeType = getMimeType(img.base64_data);

                            return (
                                <div
                                    key={idx}
                                    className="rounded-lg overflow-hidden border-2 border-orange-500/20 bg-orange-500/5 p-4"
                                >
                                    <div className="text-lg font-semibold mb-2">{caption}</div>
                                    <img
                                        src={`data:${mimeType};base64,${img.base64_data}`}
                                        alt={caption}
                                        className="w-full max-w-2xl rounded-lg shadow-md mb-3"
                                    />
                                    {img.explanation && (
                                        <div className="text-sm bg-white/50 rounded-md p-3 leading-relaxed">
                                            <strong className="text-gray-700">📝 Explanation:</strong>{' '}
                                            {img.explanation}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default DiagramDisplay;
