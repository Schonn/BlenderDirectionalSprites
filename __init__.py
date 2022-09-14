# Viewport Directional Sprites
# Copyright (C) 2022 Pierre
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of  MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

#import blender python libraries
import bpy
import math
import mathutils

#addon info read by Blender
bl_info = {
    "name": "Viewport Directional Sprites",
    "author": "Pierre",
    "version": (0, 0, 1),
    "blender": (3, 2, 2),
    "description": "Create and display directional sprites in the blender viewport",
    "category": "Animation"
    }

#panel class for setup, start and stop
class VIEWSPRITES_PT_Settings(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'ViewSprite Settings'
    bl_context = 'objectmode'
    bl_category = 'Viewport Directional Sprites'
    bpy.types.Scene.VIEWSPRITESStopSignal = bpy.props.BoolProperty(name="Stop Sprites Updating",description="Stop viewport directional sprites from updating",default=True)
    bpy.types.Scene.VIEWSPRITESChunkSize = bpy.props.IntProperty(name="Scene Iteration Chunk Size",description="How many scene items to iterate in a chunk per tick",default=10,min=1, max=1000)

    def draw(self, context):
        self.layout.prop(context.scene,"VIEWSPRITESChunkSize")
        self.layout.operator('viewsprites.startviewsprites', text ='Start Updating Viewport Directional Sprites')
        self.layout.operator('viewsprites.stopviewsprites', text ='Stop Updating Viewport Directional Sprites')

#function to begin modal running
class VIEWSPRITES_OT_StartViewSprites(bpy.types.Operator):
    bl_idname = "viewsprites.startviewsprites"
    bl_label = "Start Viewport Directional Sprites"
    bl_description = "Start updating Viewport Directional Sprites"
    
    #timer for running modal and settings for iterating through scene in chunks
    VIEWSPRITESTimer = None
    chunkIteration = 0

    def modal(self, context, event):
        #stop modal timer if the stop signal is activated
        if(context.scene.VIEWSPRITESStopSignal == True):
            context.window_manager.event_timer_remove(self.VIEWSPRITESTimer)
            self.report({'INFO'},"Viewport Directional Sprites stopped updating.")
            return {'CANCELLED'}
        #variables used during iteration
        chosen3DUpdateArea = None
        copyRotationOnlyMatrix = None
        objectUVData = None
        objectParent = None
        centerUVPosition = mathutils.Vector((0.531,0.5))
        islandUVPosition = centerUVPosition
        
        #pick the first 3D viewport to get view rotation from
        for potential3DArea in bpy.data.window_managers[0].windows[0].screen.areas:
            if(potential3DArea.type == 'VIEW_3D'):
                chosen3DUpdateArea = potential3DArea.spaces[0].region_3d
                break
        #if a 3D viewport is available, perform updates
        if(chosen3DUpdateArea != None):
            #set chunk size to max, or to the scene object list length if the scene is small
            chunkSizeAdjusted = bpy.context.scene.VIEWSPRITESChunkSize
            if(chunkSizeAdjusted > len(bpy.context.scene.objects)):
                chunkSizeAdjusted = len(bpy.context.scene.objects)
            #iterate through scene objects in chunks
            for chunkStep in range(0,chunkSizeAdjusted):
                if(self.chunkIteration < len(bpy.context.scene.objects)):
                    iterationObject = bpy.context.scene.objects[self.chunkIteration]
                    #only work with objects that have custom property VIEWSPRITECARD
                    if((("VIEWSPRITECARD" in iterationObject) == True)):
                        #use the card's original location and scale, with the view's rotation, combine them in a new world matrix and apply it to the card
                        copyRotationOnlyMatrix = mathutils.Matrix.LocRotScale(iterationObject.matrix_world.translation,chosen3DUpdateArea.view_rotation,iterationObject.matrix_world.to_scale())
                        iterationObject.matrix_world = copyRotationOnlyMatrix
                        #shift uv to match rotation
                        objectParent = iterationObject.parent
                        
                        
                        islandUVPosition += mathutils.Vector((0.0625*round(chosen3DUpdateArea.view_rotation.to_euler()[2]*2.5),0.11*round((-chosen3DUpdateArea.view_rotation.to_euler()[0]+1.5)*2.5)))
                        
                        objectUVData = iterationObject.data.uv_layers[0].data
                        objectUVData[0].uv = islandUVPosition + mathutils.Vector((-0.03,-0.05))
                        objectUVData[1].uv = islandUVPosition + mathutils.Vector((+0.03,-0.05))
                        objectUVData[2].uv = islandUVPosition + mathutils.Vector((+0.03,+0.05))
                        objectUVData[3].uv = islandUVPosition + mathutils.Vector((-0.03,+0.05))
                        #for uvPoint in iterationObject.data.uv_layers[0].data:
                        #    uvPoint.uv += mathutils.Vector((0.001,0))
                        
                    self.chunkIteration += 1
                else:
                    self.chunkIteration = 0
        return {'PASS_THROUGH'}

    def execute(self, context):
        if(context.scene.VIEWSPRITESStopSignal == True):
            context.scene.VIEWSPRITESStopSignal = False
            self.VIEWSPRITESTimer = context.window_manager.event_timer_add(0.001, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.report({'INFO'},"Viewport Directional Sprites started updating.")
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'},"'Start Viewport Directional Sprites' was pressed, but Viewport Directional Sprites are already updating.")
            return {'FINISHED'}
        
        
#function to stop modal running
class VIEWSPRITES_OT_StopViewSprites(bpy.types.Operator):
    bl_idname = "viewsprites.stopviewsprites"
    bl_label = "Stop Viewport Directional Sprites"
    bl_description = "Stop updating Viewport Directional Sprites"
    
    #turn on the stop signal switch
    def execute(self, context):
        context.scene.VIEWSPRITESStopSignal = True
        return {'FINISHED'}
    
#register and unregister
actlodClasses = (  VIEWSPRITES_PT_Settings,
                    VIEWSPRITES_OT_StartViewSprites,
                    VIEWSPRITES_OT_StopViewSprites
                    )

register, unregister = bpy.utils.register_classes_factory(actlodClasses)

if __name__ == '__main__':
    register()


    
