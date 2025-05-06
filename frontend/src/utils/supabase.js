import { createClient } from '@supabase/supabase-js'

// Confirm environment variables are correctly loaded
console.log('Supabase URL:', import.meta.env.VITE_SUPABASE_URL)
console.log('Supabase Anon Key:', import.meta.env.VITE_SUPABASE_ANON_KEY)

// Create the Supabase client
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
)

/**
 * Uploads a file to the 'images' bucket in Supabase Storage
 * @param {File} file - The file to upload
 * @param {string} [folder='uploads'] - Optional folder path inside the bucket
 * @returns {Promise<{data: object|null, error: string|null}>}
 */
export const uploadImageToSupabase = async (file, folder = 'uploads') => {
  try {
    const filePath = `${folder}/${Date.now()}_${file.name}`

    const { data, error } = await supabase.storage
      .from('images')
      .upload(filePath, file, { upsert: true })

    if (error) {
      console.error('❌ Upload error:', error.message || error)
      return { data: null, error: error.message }
    }

    console.log('✅ Image uploaded successfully:', data)
    return { data, error: null }
  } catch (err) {
    console.error('❌ Unexpected error during upload:', err)
    return { data: null, error: err.message || 'Unexpected error' }
  }
}
