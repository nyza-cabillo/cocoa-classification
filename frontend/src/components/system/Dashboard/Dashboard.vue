<template>
  <div class="dashboard-container">
    <h1 class="title">
      Cocoa Pod Disease Classifier<button @click="handleLogout" class="logout-button">
        Logout
      </button>
    </h1>

    <div class="content">
      <!-- Left Column -->
      <div class="left-column">
        <div class="upload-box">
          <h3>Upload a Cocoa Pod Image</h3>
          <input type="file" ref="fileInput" @change="handleImageUpload" />
        </div>
        <div class="button-group">
          <button @click="clearImage" class="clear-btn">Clear</button>
          <button @click="submitImage" class="submit-btn">Submit</button>
        </div>

        <label for="feedback">Your Feedback:</label>
        <textarea
          id="feedback"
          v-model="feedback"
          placeholder="What do you think about the prediction?"
        ></textarea>
        <button @click="submitFeedback">Submit Feedback</button>

        <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
        <p v-if="error" class="error-message">{{ error }}</p>
      </div>

      <!-- Right Column -->
      <div class="right-column">
        <h3>Inputted Image</h3>
        <div v-if="imagePreview">
          <img :src="imagePreview" alt="Preview" class="image-preview" />
        </div>

        <p v-if="predictionResult">
          <strong>Prediction:</strong> {{ predictionResult }} (Confidence:
          {{ predictionConfidence }}%)
        </p>

        <div v-if="perModelResults" class="prediction-result">
          <h4>Model Predictions:</h4>
          <pre>{{ perModelResults }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { supabase } from '@/utils/supabase'

export default {
  data() {
    return {
      feedback: '',
      error: '',
      successMessage: '',
      predictionId: '', // Corrected variable usage
      imagePreview: '', // Add imagePreview to the data
      predictionResult: '', // Ensure to have this for displaying predictions
      predictionConfidence: '', // To show prediction confidence
    }
  },
  methods: {
    clearImage() {
      this.imagePreview = ''
      this.predictionResult = ''
      this.predictionConfidence = ''
      this.feedback = ''
      this.$refs.fileInput.value = ''
    },

    async submitImage() {
      this.error = ''
      this.successMessage = ''

      // Ensure the user is logged in
      const {
        data: { user },
        error: userError,
      } = await supabase.auth.getUser()

      if (userError || !user) {
        this.error = 'You must be logged in to submit an image.'
        return
      }

      const fileInput = this.$refs.fileInput
      const file = fileInput.files[0]

      if (!file) {
        this.error = 'Please upload an image before submitting.'
        return
      }

      try {
        // 1. Upload image to Supabase Storage
        const filePath = `images/${Date.now()}_${file.name}`
        const { error: uploadError } = await supabase.storage
          .from('images') // Your storage bucket name
          .upload(filePath, file)

        if (uploadError) {
          this.error = 'Failed to upload image to storage.'
          console.error(uploadError.message)
          return
        }

        const imageUrl = supabase.storage.from('images').getPublicUrl(filePath).data.publicUrl

        // 2. Save image metadata to Supabase DB
        const { data: imageData, error: imageInsertError } = await supabase
          .from('image')
          .insert([{ user_id: user.id, image_url: imageUrl }])
          .select()
          .single()

        if (imageInsertError) {
          this.error = 'Error saving image metadata.'
          return
        }

        // 3. Send image to Flask backend for prediction
        const formData = new FormData()
        formData.append('image', file)

        const response = await fetch('http://127.0.0.1:5000/predict', {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          throw new Error('Prediction request failed.')
        }

        const predictionResponse = await response.json()
        const predicted_class = predictionResponse.prediction
        const confidence = predictionResponse.confidence

        // 4. Save prediction to Supabase
        const { data: predictionData, error: predictionInsertError } = await supabase
          .from('prediction')
          .insert([
            {
              image_id: imageData.id,
              predicted_class,
              confidence,
            },
          ])
          .select()
          .single()

        if (predictionInsertError) {
          this.error = 'Error saving prediction to database.'
          return
        }

        // 5. Update frontend display
        this.imagePreview = imageUrl
        this.predictionResult = predicted_class
        this.predictionConfidence = confidence
        this.predictionId = predictionData.id
        this.successMessage = 'Prediction completed successfully!'
      } catch (err) {
        console.error(err)
        this.error = 'An error occurred during prediction.'
      }
    },

    async submitFeedback() {
      // Get current user
      const {
        data: { user },
        error: userError,
      } = await supabase.auth.getUser()

      if (userError || !user) {
        this.error = 'You must be logged in to submit feedback.'
        return
      }

      // Insert feedback
      const { error } = await supabase.from('feedback').insert([
        {
          user_id: user.id,
          prediction_id: this.predictionId,
          feedback_text: this.feedback,
        },
      ])

      if (error) {
        console.error('Error submitting feedback:', error.message)
        this.error = 'Failed to submit feedback.'
        return
      }

      // Success
      this.feedback = ''
      this.successMessage = 'Feedback submitted successfully!'
      this.error = ''
    },
  },
}
</script>

<style src="./Dashboard.css"></style>
