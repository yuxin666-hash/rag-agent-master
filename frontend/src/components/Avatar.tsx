import { useState } from 'react'

const IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.webp', '.gif']

interface AvatarProps {
  basePath: string
  fallbackGradient: string
  label: string
}

export default function Avatar({ basePath, fallbackGradient, label }: AvatarProps) {
  const [formatIndex, setFormatIndex] = useState(0)
  const [loaded, setLoaded] = useState(false)
  const [allFailed, setAllFailed] = useState(false)

  const currentSrc = `${basePath}${IMAGE_FORMATS[formatIndex]}`
  const showImg = loaded && !allFailed

  const handleLoad = () => {
    setLoaded(true)
  }

  const handleError = () => {
    if (formatIndex < IMAGE_FORMATS.length - 1) {
      setFormatIndex((prev) => prev + 1)
    } else {
      setAllFailed(true)
    }
  }

  return (
    <div style={{ position: 'relative', width: '34px', height: '34px', flexShrink: 0 }}>
      {!showImg && (
        <div
          style={{
            width: '34px',
            height: '34px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px',
            background: fallbackGradient,
            color: '#fff',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          {label}
        </div>
      )}
      <img
        src={currentSrc}
        onLoad={handleLoad}
        onError={handleError}
        style={{
          width: '34px',
          height: '34px',
          borderRadius: '10px',
          objectFit: 'cover',
          display: showImg ? 'block' : 'none',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}
      />
    </div>
  )
}
