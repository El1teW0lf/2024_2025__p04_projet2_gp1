from panda3d.core import loadPrcFileData, WindowProperties
from controller import PlayerController
from modules import parse_json
import os
from menus import PauseMenu, CodeMenu
from panda3d.bullet import BulletWorld
from panda3d.bullet import BulletPlaneShape, BulletRigidBodyNode
from panda3d.core import Vec3,BitMask32
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.bullet import BulletDebugNode
from panda3d.bullet import BulletBoxShape
from panda3d.core import CollisionRay, CollisionNode, CollisionTraverser, CollisionHandlerQueue, GeomNode

configVars = """
win-size 1280 720
show-frame-rate-meter 1
"""
loadPrcFileData("", configVars)
loadPrcFileData("", "gl-version 3 2")


class TestWorld():
    def __init__(self,base):

        self.base = base

        self.base.reset()

        self.paused = False
        self.coding = False

        self.userExit = base.userExit

        self.base.disableMouse()

        self.bullet_world = self.base.bullet_world

        self.base.setBackgroundColor(0,0,0)

        self.computer_path = "assets/Mesh_Monitor_06/model.fbx"

        #self.base.oobe()

        self.camera = self.base.camera
        self.loader = self.base.loader
        self.render = self.base.render

        self.camera.setPos(0, 0, 0)
        self.camera.setHpr(0, 0, 0)

        shape = BulletPlaneShape(Vec3(0, 0, 100), 0)

        floor = BulletRigidBodyNode('Ground')
        floorNP = self.render.attachNewNode(floor)
        floorNP.node().addShape(shape)
        floorNP.node().setMass(0)
        floorNP.setPos(0, 0, 0)
        floorNP.setCollideMask(BitMask32.bit(1))
        self.bullet_world.attachRigidBody(floorNP.node())

        shape = BulletPlaneShape(Vec3(0, 0, -1), 1)
        body = BulletRigidBodyNode('Ground')
        bodyNP = self.render.attachNewNode(body)
        bodyNP.node().addShape(shape)
        bodyNP.node().setMass(0)
        bodyNP.setPos(0, 0, 30)
        bodyNP.setCollideMask(BitMask32.bit(1))

        self.bullet_world.attachRigidBody(bodyNP.node())
        self.controller = PlayerController(self.base)

        script_directory = os.path.dirname(os.path.realpath(__file__))
        folder_path = os.path.join(script_directory, "test_scene_2")

        self.base.camLens.setFov(90)
        parse_json(folder_path, self.render, self.loader, "scenes/test_scene_2", self.bullet_world)

        props = WindowProperties()
        props.setFullscreen(True)
        #self.win.requestProperties(props)

        screen_aspect_ratio = self.base.win.getProperties().getXSize() / self.base.win.getProperties().getYSize()
        self.base.camLens.setAspectRatio(screen_aspect_ratio)

        self.menu = PauseMenu(self)
        self.code_menu = CodeMenu(self)

        self.show_debug_collision = False

        debugNode = BulletDebugNode('Debug')
        debugNode.showWireframe(self.show_debug_collision)
        debugNode.showConstraints(self.show_debug_collision)
        debugNode.showBoundingBoxes(self.show_debug_collision)
        debugNode.showNormals(self.show_debug_collision)
        debugNP = self.render.attachNewNode(debugNode)
        debugNP.show()

        self.bullet_world.setDebugNode(debugNP.node())

        self.picker_ray = CollisionRay()
        self.picker_node = CollisionNode("mouseRay")
        self.picker_node.addSolid(self.picker_ray)
        self.picker_node.setFromCollideMask(GeomNode.getDefaultCollideMask())  # Detect all geometry
        self.picker_np = self.camera.attachNewNode(self.picker_node)

        # Collision traverser and handler
        self.collision_traverser = CollisionTraverser()
        self.collision_handler = CollisionHandlerQueue()
        self.collision_traverser.addCollider(self.picker_np, self.collision_handler)

        # Mouse click detection
        self.base.accept("mouse1", self.on_click)

        self.base.accept("escape", self.toggle_pause_menu)
        self.base.taskMgr.add(self.update, 'draw_debug_world')

    def toggle_pause_menu(self):
        if not self.paused:
            self.controller.pause()
            self.menu.show()
            self.paused = not self.paused
        else:
            self.menu.hide()
            self.controller.run()
            self.paused = not self.paused

    def toggle_code_menu(self):
        if not self.coding:
            self.controller.pause()
            self.code_menu.show()
            self.coding = not self.coding
        else:
            self.code_menu.hide()
            self.controller.run()
            self.coding = not self.coding

    def update(self,task):
        if not self.paused and not self.coding:
            self.bullet_world.doPhysics(globalClock.getDt())
        return task.cont
    
    def on_click(self):
        if self.base.mouseWatcherNode.hasMouse():
            # Get mouse position and set ray origin/direction
            mpos = self.base.mouseWatcherNode.getMouse()
            self.picker_ray.setFromLens(self.base.camNode, mpos.getX(), mpos.getY())

            # Traverse collisions
            self.collision_traverser.traverse(self.render)

            if self.collision_handler.getNumEntries() > 0:
                # Get the closest object
                self.collision_handler.sortEntries()
                picked_obj = self.collision_handler.getEntry(0).getIntoNodePath()

                # Find the tagged parent node
                picked_obj = picked_obj.findNetTag("Clickable")
                if not picked_obj.isEmpty():
                    self.handle_picked_object(picked_obj)

    def handle_picked_object(self, picked_obj):
        if picked_obj.getTag('Clickable') == self.computer_path:
            print(f"Launched Computer")
            self.toggle_code_menu()
            

if __name__ == "__main__":
    app = TestWorld()
    app.run()
