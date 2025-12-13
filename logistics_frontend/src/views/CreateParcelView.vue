<template>
  <div class="page-container">
    <h2>Create Parcel</h2>
    <el-form :model="form" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card header="Sender Info">
            <el-form-item label="Name">
              <el-input v-model="form.sender.name" />
            </el-form-item>
            <el-form-item label="Phone">
              <el-input v-model="form.sender.phone" />
            </el-form-item>
            <el-form-item label="Address">
              <el-input v-model="form.sender.address" />
            </el-form-item>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card header="Receiver Info">
            <el-form-item label="Name">
              <el-input v-model="form.receiver.name" />
            </el-form-item>
            <el-form-item label="Phone">
              <el-input v-model="form.receiver.phone" />
            </el-form-item>
            <el-form-item label="Address">
              <el-input v-model="form.receiver.address" />
            </el-form-item>
          </el-card>
        </el-col>
      </el-row>

      <el-card header="Parcel Details" style="margin-top: 20px;">
        <el-form-item label="Weight (kg)">
          <el-input-number v-model="form.weight" :precision="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="Volume">
          <el-input v-model="form.volume" placeholder="e.g., 10x10x10" />
        </el-form-item>
        <el-form-item label="Start Station ID">
          <el-input-number v-model="form.start_station_id" />
        </el-form-item>
        <el-form-item label="Final Station ID">
          <el-input-number v-model="form.final_station_id" />
        </el-form-item>
      </el-card>

      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="handleSubmit">Create Parcel</el-button>
      </div>
    </el-form>

    <el-dialog v-model="dialogVisible" title="Parcel Created">
      <p>Tracking Number: <strong>{{ createdTrackingNumber }}</strong></p>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="dialogVisible = false">OK</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { createParcel } from '@/api/logistics'
import { ElMessage } from 'element-plus'

const form = ref({
  weight: 1.0,
  volume: '',
  sender: {
    name: '',
    phone: '',
    address: ''
  },
  receiver: {
    name: '',
    phone: '',
    address: ''
  },
  start_station_id: 1,
  final_station_id: 2
})

const dialogVisible = ref(false)
const createdTrackingNumber = ref('')

const handleSubmit = async () => {
  try {
    const res = await createParcel(form.value)
    createdTrackingNumber.value = res.tracking_number
    dialogVisible.value = true
    ElMessage.success('Parcel created successfully')
  } catch (error) {
    ElMessage.error('Failed to create parcel: ' + (error.response?.data?.detail || error.message))
  }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}
</style>
