import { createClient } from '@supabase/supabase-js'

// Create the Supabase client using the Vite environment variables
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL, // Vite env variable for Supabase URL
  import.meta.env.VITE_SUPABASE_ANON_KEY, // Vite env variable for anon key
)
/**
 * Uploads a file to the 'images' bucket in Supabase Storage
 * @param {File} file - The file to upload
 * @param {string} [folder='uploads'] - Optional folder path inside the bucket
 * @param {string} [authToken] - Optional authentication token
 * @returns {Promise<{data: object|null, error: string|null}>}
 */

export const uploadImageToSupabase = async (file, folder = 'uploads', authToken = null) => {
  try {
    const filePath = `${folder}/${Date.now()}_${file.name}`

    const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {}

    const { data, error } = await supabase.storage.from('images').upload(filePath, file, {
      upsert: true,
      headers, // Adding headers only if authToken is passed
    })

    if (error) {
      console.error('Upload error:', error.message || error)
      return { data: null, error: error.message }
    }

    console.log('Image uploaded successfully:', data)
    return { data, error: null }
  } catch (err) {
    console.error('Unexpected error during upload:', err)
    return { data: null, error: err.message || 'Unexpected error' }
  }
}
