<template>
  <div class="dashboard-container">
    <h1 class="title">
      Cocoa Pod Disease Classifier
      <button @click="handleLogout" class="logout-button">Logout</button>
    </h1>

    <div class="content">
      <!-- Left Column -->
      <div class="left-column">
        <div class="upload-box">
          <h3>Upload a Cocoa Pod Image</h3>
          <input type="file" ref="fileInput" @change="handleFileChange" />
        </div>
        <div class="button-group">
          <button @click="clearImage" class="clear-btn">Clear</button>
          <button @click="submitImage" class="submit-btn">Submit</button>
        </div>
        <div class="feedback">
          <label for="feedback">Your Feedback:</label>
          <textarea
            class="feedback-textarea"
            id="feedback"
            v-model="feedback"
            placeholder="What do you think about the prediction?"
          ></textarea>
          <button class="feedback-button" @click="submitFeedback">Submit Feedback</button>

          <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
          <p v-if="error" class="error-message">{{ error }}</p>
        </div>
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
import { uploadImageToSupabase } from '@/utils/supabase'

export default {
  data() {
    return {
      feedback: '',
      error: '',
      successMessage: '',
      predictionId: '',
      imagePreview: '',
      predictionResult: '',
      predictionConfidence: '',
      perModelResults: '',
      imageFile: null,
    }
  },
  methods: {
    handleFileChange(e) {
      this.imageFile = e.target.files[0]
    },

    clearImage() {
      this.imagePreview = ''
      this.predictionResult = ''
      this.predictionConfidence = ''
      this.feedback = ''
      this.$refs.fileInput.value = ''
      this.successMessage = ''
      this.error = ''
      this.imageFile = null
    },

    async handleUpload() {
      if (!this.imageFile) {
        this.error = 'No image selected.'
        return
      }

      const result = await uploadImageToSupabase(this.imageFile)

      if (result.error) {
        this.error = result.error
        this.successMessage = ''
      } else {
        this.successMessage = 'Image uploaded successfully!'
        this.error = ''
        console.log('Uploaded path:', result.data.path)
      }
    },

    async submitImage() {
      this.error = ''
      this.successMessage = ''

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
        const filePath = `images/${Date.now()}_${file.name}`
        const { error: uploadError } = await supabase.storage.from('images').upload(filePath, file)

        if (uploadError) {
          this.error = 'Failed to upload image to storage.'
          console.error(uploadError.message)
          return
        }

        const imageUrl = supabase.storage.from('images').getPublicUrl(filePath).data.publicUrl

        const { data: imageData, error: imageInsertError } = await supabase
          .from('image')
          .insert([{ user_id: user.id, image_url: imageUrl }])
          .select()
          .single()

        if (imageInsertError) {
          this.error = 'Error saving image metadata.'
          return
        }

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
      const {
        data: { user },
        error: userError,
      } = await supabase.auth.getUser()

      if (userError || !user) {
        this.error = 'You must be logged in to submit feedback.'
        return
      }

      try {
        const response = await fetch('http://127.0.0.1:5000/submit_feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: user.id,
            prediction_id: this.predictionId,
            feedback_text: this.feedback,
          }),
        })

        if (!response.ok) {
          throw new Error('Feedback submission failed.')
        }

        const feedbackResponse = await response.json()
        this.successMessage = feedbackResponse.message || 'Feedback submitted successfully!'
        this.error = ''
        this.feedback = ''
      } catch (err) {
        console.error(err)
        this.error = 'An error occurred during feedback submission.'
      }
    },

    async handleLogout() {
      try {
        await supabase.auth.signOut()
        this.$router.push('/login')
      } catch (error) {
        console.error('Error during logout:', error.message)
      }
    },
  },
}
</script>

<style src="./Dashboard.css"></style>
