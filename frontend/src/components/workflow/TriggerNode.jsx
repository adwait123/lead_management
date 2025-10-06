import React from 'react'
import { Handle, Position } from '@xyflow/react'

const TriggerNode = ({ data }) => {
  return (
    <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4 min-w-[200px] shadow-sm hover:shadow-md transition-shadow">
      {/* Output handle (right side) */}
      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: '#3b82f6',
          width: 12,
          height: 12,
          border: '2px solid white'
        }}
      />

      <div className="flex items-start space-x-3">
        <div className="text-2xl">{data.icon || '⚡'}</div>
        <div className="flex-1">
          <div className="font-semibold text-blue-900 text-sm">{data.label}</div>
          <div className="text-xs text-blue-700 mt-1">{data.description}</div>
          <div className="mt-2">
            <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
              {data.triggerType}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TriggerNode