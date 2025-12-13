<template>
  <div class="page-container">
    <h2>Last Mile Delivery</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="Assign Delivery" name="assign">
        <el-form :model="assignForm" label-width="120px" style="max-width: 600px;">
          <el-form-item label="Courier ID">
            <el-input-number v-model="assignForm.courier_id" />
          </el-form-item>
          <el-form-item label="Parcel IDs">
            <el-input
              v-model="parcelIdsInput"
              placeholder="Comma separated tracking numbers"
              type="textarea"
            />
            <div class="hint">Enter tracking numbers separated by commas</div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleAssign">Assign to Courier</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="Update Delivery Status" name="update">
        <el-form :model="updateForm" label-width="120px" style="max-width: 600px;">
          <el-form-item label="Parcel ID">
            <el-input v-model="updateForm.parcel_id" placeholder="Tracking Number" />
          </el-form-item>
          <el-form-item label="New Status">
            <el-select v-model="updateForm.status">
              <el-option label="Start Delivery" value="start" />
              <el-option label="Finish Delivery" value="finish" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleUpdateStatus">Update Status</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { createDeliveryTask, updateDeliveryStatus } from '@/api/logistics'
import { ElMessage } from 'element-plus'

const activeTab = ref('assign')

// Assign Delivery
const assignForm = ref({
  courier_id: 1,
  parcel_ids: []
})
const parcelIdsInput = ref('')

const handleAssign = async () => {
  const ids = parcelIdsInput.value.split(',').map(id => id.trim()).filter(id => id)
  if (ids.length === 0) {
    ElMessage.warning('Please enter at least one parcel ID')
    return
  }

  try {
    const payload = {
      ...assignForm.value,
      parcel_ids: ids
    }
    await createDeliveryTask(payload)
    ElMessage.success('Delivery tasks assigned successfully')
  } catch (error) {
    ElMessage.error('Failed to assign tasks: ' + (error.response?.data?.detail || error.message))
  }
}

// Update Status
const updateForm = ref({
  parcel_id: '',
  status: 'start'
})

const handleUpdateStatus = async () => {
  if (!updateForm.value.parcel_id) {
    ElMessage.warning('Please enter a parcel ID')
    return
  }
  try {
    await updateDeliveryStatus(updateForm.value)
    ElMessage.success('Delivery status updated')
  } catch (error) {
    ElMessage.error('Failed to update status: ' + (error.response?.data?.detail || error.message))
  }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.hint {
  font-size: 12px;
  color: #999;
}
</style>
