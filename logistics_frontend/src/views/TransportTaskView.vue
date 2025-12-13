<template>
  <div class="page-container">
    <h2>Transport Management</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="Create Transport Task" name="create">
        <el-form :model="createForm" label-width="120px" style="max-width: 600px;">
          <el-form-item label="Driver ID">
            <el-input-number v-model="createForm.driver_id" />
          </el-form-item>
          <el-form-item label="Vehicle ID">
            <el-input-number v-model="createForm.vehicle_id" />
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
            <el-button type="primary" @click="handleCreateTask">Create Task</el-button>
          </el-form-item>
        </el-form>
        <div v-if="createdTask" class="result-box">
          <p>Task Created!</p>
          <p>Task Code: <strong>{{ createdTask.task_code }}</strong></p>
          <p>Task ID: {{ createdTask.task_id }}</p>
        </div>
      </el-tab-pane>

      <el-tab-pane label="Update Task Status" name="update">
        <el-form :model="updateForm" label-width="120px" style="max-width: 600px;">
          <el-form-item label="Task Code">
            <el-input v-model="updateForm.task_code" />
          </el-form-item>
          <el-form-item label="New Status">
            <el-select v-model="updateForm.status">
              <el-option label="In Transit" value="in_transit" />
              <el-option label="Completed" value="completed" />
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
import { ref, computed } from 'vue'
import { createTransportTask, updateTransportStatus } from '@/api/logistics'
import { ElMessage } from 'element-plus'

const activeTab = ref('create')

// Create Task
const createForm = ref({
  driver_id: 1,
  vehicle_id: 1,
  parcel_ids: []
})
const parcelIdsInput = ref('')
const createdTask = ref(null)

const handleCreateTask = async () => {
  // Parse parcel IDs
  const ids = parcelIdsInput.value.split(',').map(id => id.trim()).filter(id => id)
  if (ids.length === 0) {
    ElMessage.warning('Please enter at least one parcel ID')
    return
  }
  
  try {
    const payload = {
      ...createForm.value,
      parcel_ids: ids
    }
    const res = await createTransportTask(payload)
    createdTask.value = res
    ElMessage.success('Transport task created')
  } catch (error) {
    ElMessage.error('Failed to create task: ' + (error.response?.data?.detail || error.message))
  }
}

// Update Status
const updateForm = ref({
  task_code: '',
  status: 'in_transit'
})

const handleUpdateStatus = async () => {
  if (!updateForm.value.task_code) {
    ElMessage.warning('Please enter a task code')
    return
  }
  try {
    await updateTransportStatus(updateForm.value)
    ElMessage.success('Task status updated')
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
.result-box {
  margin-top: 20px;
  padding: 15px;
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
  border-radius: 4px;
}
</style>
