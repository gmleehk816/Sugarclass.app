
import React, { useRef } from 'react';
import { FileData } from '../types';
import { uploadFile } from '../services/apiService';

interface FileUploadProps {
  onFilesSelected: (files: FileData[]) => void;
  selectedFiles: FileData[];
  onUploadStart?: () => void;
  onUploadEnd?: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFilesSelected,
  selectedFiles,
  onUploadStart,
  onUploadEnd
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    onUploadStart?.();
    const newFiles: FileData[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      try {
        const pendingFile: FileData = {
          name: file.name,
          type: file.type,
          size: file.size,
          status: 'uploading'
        };

        // Add pending file immediately
        onFilesSelected([...selectedFiles, ...newFiles, pendingFile]);

        if (file.type.startsWith('image/')) {
          const reader = new FileReader();
          const base64Promise = new Promise<string>((resolve) => {
            reader.onload = (event) => resolve(event.target?.result as string);
            reader.readAsDataURL(file);
          });
          pendingFile.base64 = await base64Promise;
        }

        const uploadResult = await uploadFile(file);

        const processedFile: FileData = {
          ...pendingFile,
          id: uploadResult.file_id,
          status: 'processed',
          message: uploadResult.message
        };

        newFiles.push(processedFile);
        onFilesSelected([...selectedFiles, ...newFiles]);
      } catch (error: any) {
        console.error(`Failed to upload ${file.name}:`, error);
        const errorFile: FileData = {
          name: file.name,
          type: file.type,
          size: file.size,
          status: 'error',
          message: error.message || 'Upload failed'
        };
        newFiles.push(errorFile);
        onFilesSelected([...selectedFiles, ...newFiles]);
      }
    }

    onUploadEnd?.();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="flex items-center gap-2">
      <input
        type="file"
        multiple
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".txt,.md,.pdf,image/*"
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        className="p-3 bg-white/50 hover:bg-white rounded-xl transition-colors text-[#332F33] flex items-center justify-center border border-[#332F33]/10"
        title="Upload context documents"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
        </svg>
      </button>
    </div>
  );
};

export default FileUpload;
