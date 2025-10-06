import React from 'react'
import { Handle, Position } from '@xyflow/react'

const AgentNode = ({ data }) => {
  return (
    <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4 min-w-[200px] shadow-sm hover:shadow-md transition-shadow">
      {/* Input handle (left side) */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: '#10b981',
          width: 12,
          height: 12,
          border: '2px solid white'
        }}
      />

      <div className="flex items-start space-x-3">
        <div className="text-2xl">🤖</div>
        <div className="flex-1">
          <div className="font-semibold text-green-900 text-sm">{data.label}</div>
          {data.description && (
            <div className="text-xs text-green-700 mt-1">{data.description}</div>
          )}
          <div className="mt-2 space-y-1">
            <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full mr-1">
              {data.useCase || 'general'}
            </span>
            {data.type && (
              <span className="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">
                {data.type}
              </span>
            )}
          </div>
          {data.agentId && (
            <div className="text-xs text-gray-500 mt-1">
              Agent ID: {data.agentId}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AgentNode