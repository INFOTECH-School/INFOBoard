import { ExcalidrawElement } from "@excalidraw/excalidraw/types/element/types"
import {
  AppState,
  BinaryFiles,
  BinaryFileData,
  Collaborator,
  ExcalidrawImperativeAPI,
} from "@excalidraw/excalidraw/types/types"
import { RefObject, useState, useRef, useEffect } from "react"
import ReconnectingWebSocket from "reconnectingwebsocket"

import { BroadcastedExcalidrawElement, ConfigProps, PointerUpdateProps } from "../types"
import { EventEmitter, EventHandler, EventKey } from "../events"
import { reconcileElements } from "../reconciliation"
import { apiRequestInit, noop } from "../utils"
import { useEventEmitter } from "../hooks/useEventEmitter"

// #region message types
// userRoomId always gets patched into the change in the backend
export type CollaboratorChange = { time?: string; userRoomId?: string } & Collaborator

export interface CollaboratorChangeMessage {
  eventtype: "collaborator_change"
  changes: CollaboratorChange[]
}

export interface ElementsChangedMessage {
  eventtype: "elements_changed" | "full_sync"
  elements: BroadcastedExcalidrawElement[]
}

export interface FilesAddedMessage {
  eventtype: "files_added"
  fileids: string[]
}

export type CommunicatorMessage = CollaboratorChangeMessage | ElementsChangedMessage | FilesAddedMessage
// #endregion message types

export type ConnectionStates = "CONNECTED" | "DISCONNECTED"

export interface CommunicatorEventMap {
  connectionStateChanged: { state: ConnectionStates }
}

/**
 * This class and its descendants communicate with the backend via a WebSocket. Descendants may
 * implement their own message type to send and receive. They may also emit their own event types.
 */
export default class Communicator<TEventMap extends CommunicatorEventMap = CommunicatorEventMap>
  implements EventEmitter<TEventMap>
{
  protected ws: ReconnectingWebSocket
  protected config: ConfigProps

  protected _excalidrawApiRef?: RefObject<ExcalidrawImperativeAPI>
  private _connectionState: ConnectionStates = "CONNECTED"

  protected uploadedFileIds = new Set<string>()
  protected uploadingFileIds = new Set<string>()

  // #region methods for excalidraw props

  broadcastCursorMovement: (collaborator: PointerUpdateProps) => void = noop
  broadcastElements: (
    elements: readonly ExcalidrawElement[],
    appState: AppState,
    files: BinaryFiles
  ) => void = noop
  saveRoom: () => void = noop

  // #endregion methods for excalidraw props

  /**
   * Setup the WebSocket to use and configure the collaboration api.
   *
   * @param config configuration for the excalidraw room
   */
  constructor(config: ConfigProps, ws: ReconnectingWebSocket) {
    // collaborator setup
    this.config = config

    // websocket setup
    this.ws = ws

    this.ws.addEventListener("message", (event) => {
      this.routeMessage(JSON.parse(event.data))
    })

    // code 3000 is sent when a disconnect happens due to an authentication error.
    this.ws.addEventListener("connecting", (event) => {
      event.code == 3000 && this.ws.close()
    })
  }

  // #region component communication
  /**
   * This needs to be called when the excalidraw component is set up!
   */
  set excalidrawApiRef(apiRef: RefObject<ExcalidrawImperativeAPI>) {
    this._excalidrawApiRef = apiRef
  }

  /**
   * Helper to access the excalidraw api more easily
   */
  protected get excalidrawApi() {
    if (!this._excalidrawApiRef) {
      throw new Error("The excalidrawApiRef has not been set yet.")
    }
    return this._excalidrawApiRef.current
  }

  get connectionState() {
    return this._connectionState
  }

  private handlers: {
    [Parameter in keyof TEventMap]?: Set<(event: TEventMap[Parameter]) => void>
  } = {}

  /**
   * Emits an event on the Communicator.
   *
   * @param eventName event to emit
   * @param event event data
   */
  emit<K extends EventKey<TEventMap>>(eventName: K, event: TEventMap[K]): void {
    this.handlers[eventName]?.forEach((handler) => handler(event))
  }

  /**
   * Register an event on the Communicator.
   *
   * @param eventName event to register. Supported: connectionStateChange
   * @param handler event handler
   */
  on<K extends EventKey<TEventMap>>(eventName: K, handler: EventHandler<TEventMap, K>): void {
    if (!this.handlers[eventName]) {
      this.handlers[eventName] = new Set()
    }
    this.handlers[eventName]?.add(handler)
  }

  /**
   * Unregister a previously registered event.
   *
   * @param eventName event to unregister
   * @param handler handler to unregister
   */
  off<K extends EventKey<TEventMap>>(eventName: K, handler: EventHandler<TEventMap, K>): void {
    this.handlers[eventName]?.delete(handler)
  }
  // #endregion component communication

  // #region message hadling
  /**
   * Looks up which message type (`eventtype`) was sent by the
   * backend and calls the appropriate method to process it.
   *
   * @param message message sent by a collaborator
   *
   * @returns is the message was routed
   */
  protected routeMessage<MsgType extends CommunicatorMessage>(message: MsgType): boolean {
    switch (message.eventtype) {
      case "collaborator_change":
        // if a buffer was sent, only the last change and any
        // additional information is relevant to this client
        this.receiveCollaboratorChange(
          message.changes.reduce((acc, current) => Object.assign(acc, current), {})
        )
        return true
      case "elements_changed":
      case "full_sync":
        this.receiveElements(message.elements)
        return true
      case "files_added":
        this.receiveFiles(message.fileids)
        return true
      default:
        return false
    }
  }

  /**
   * Get a url for a file to upload or download.
   *
   * @param fileId the files id
   * @returns a url for the file with the given id
   */
  protected fileUrl(fileId: string) {
    return this.config.FILE_URL_TEMPLATE!.replace("FILE_ID", fileId)
  }

  protected nextTryTimeout(nextTryExponentMinusOne: number) {
    return Math.min(
      this.config.UPLOAD_RETRY_TIMEOUT_MSEC * Math.pow(2, nextTryExponentMinusOne + 1),
      this.config.MAX_RETRY_WAIT_MSEC
    )
  }

  /**
   * Update the set of broadcasted files.
   *
   * @param newlySyncedFiles files that just have been synced
   */
  protected updateUploadedFileIDs(newlySyncedFileIds: string[]) {
    for (let index = 0; index < newlySyncedFileIds.length; index++) {
      this.uploadedFileIds.add(newlySyncedFileIds[index])
      this.uploadingFileIds.delete(newlySyncedFileIds[index])
    }
  }

  /**
   * Receive files via WebSocket.
   *
   * @param files files received over socket
   */
  private async receiveFiles(files: string[], nextTryExponentMinusOne = -1) {
    // construct requests. only files that are yet unknown are to be downloaded
    const fileRequests = files
      .filter((id) => !this.uploadedFileIds.has(id))
      .map((id) => fetch(this.fileUrl(id), apiRequestInit("GET")))

    // prevent files from being re-uploaded after this function finishes
    this.updateUploadedFileIDs(files)

    // TODO: what to do if api is not loaded yet? does this ever happen?

    // download the files and add them to the scene if the download succeeded.
    // success is defined as:
    // 1. the download promise settled
    // 2. the return status was 200. maybe this has to change in the future.
    const settledPromises = await Promise.allSettled(fileRequests)
    const succeededBinaryFileData = settledPromises
      .filter((p) => p.status == "fulfilled")
      .map((p) => (p as PromiseFulfilledResult<Response>).value)
      .filter((r) => r.status == 200)
      .map((r) => r.json() as Promise<BinaryFileData>)
    const downloadedFiles = await Promise.all(succeededBinaryFileData)
    this.excalidrawApi?.addFiles(downloadedFiles)

    // retry downloading failed IDs after a timeout elapsed
    const downloadedFileIds = downloadedFiles.map((f) => f.id as string)
    const downloadFailedIds = files.filter((id) => !downloadedFileIds.includes(id))
    if (downloadFailedIds.length) {
      setTimeout(() => {
        this.receiveFiles(downloadFailedIds, nextTryExponentMinusOne + 1)
      }, this.nextTryTimeout(nextTryExponentMinusOne))
    }
  }

  /**
   * Ends the collaboration session by closing the websocket.
   *
   * Code 3000 means "unauthorized".
   */
  protected endCollaboration() {
    console.warn("not logged in aborting session")
    this.ws.close(3000)
    this._connectionState = "DISCONNECTED"
    this.emit("connectionStateChanged", { state: this._connectionState })
  }

  // #endregion message hadling

  // #region element changes
  protected broadcastedElementsVersions = new Map<string, number>()

  /**
   * Store the versions of the elements when they were broadcasted, so it can
   * be determined which elements need to be send on the next broadcast call.
   *
   * @param elements elements on the current canvas
   */
  protected updateBroadcastedElementsVersions(elements: readonly BroadcastedExcalidrawElement[]) {
    for (let index = 0; index < elements.length; index++) {
      let element = elements[index]
      this.broadcastedElementsVersions.set(element.id, element.version)
    }
  }

  /**
   * Receive broadcasted elements from other clients.
   *
   * @param remoteElements elements that changed remotely. This can also be a full element set
   *                       if a remote client triggerd a full sync.
   */
  protected receiveElements(remoteElements: readonly BroadcastedExcalidrawElement[]) {
    if (this.excalidrawApi) {
      let reconciledElements = reconcileElements(
        this.excalidrawApi?.getSceneElementsIncludingDeleted(),
        remoteElements,
        this.excalidrawApi?.getAppState()
      )
      this.updateBroadcastedElementsVersions(reconciledElements)
      this.excalidrawApi?.updateScene({ elements: reconciledElements, commitToHistory: false })
    }
  }
  // #endregion element changes

  // #region collaborator awareness
  protected collaborators: Map<string, Collaborator> = new Map()

  /**
   * Receives the content of other clients {@link Communicator#_broadcastCursorMovement}.
   *
   * @param change an update to the collaborators
   * @returns information about the collaborator for internal usage
   */
  protected receiveCollaboratorChange(change: CollaboratorChange) {
    let userRoomId = change.userRoomId!
    let isKnownCollaborator = this.collaborators.has(userRoomId)
    let collaborator = this.collaborators.get(userRoomId) ?? {}
    delete change.userRoomId
    delete change.time
    Object.assign(collaborator, change)
    this.collaborators.set(userRoomId, collaborator)

    this.excalidrawApi?.updateScene({ collaborators: this.collaborators })

    return { isKnownCollaborator }
  }
  // #endregion collaborator awareness
}

// #region hooks

/**
 * hook into the communicator connection state
 *
 * @param communicator the commuinicator to attach to
 * @returns the current connection state
 */
export function useConnectionState(communicator: Communicator) {
  const [connectionState, setConnectionState] = useState<ConnectionStates>(
    communicator.connectionState
  )

  useEventEmitter(communicator, "connectionStateChanged", ({ state }) => {
    setConnectionState(state)
  })
  return connectionState
}

/**
 * Hook to supply the excalidraw imperative api to the communicator.
 *
 * @param communicator the communicator to supply a ref to
 * @returns the ref to be used by excalidraw
 */
export function useCommunicatorExcalidrawRef(communicator: Communicator) {
  const ref = useRef<ExcalidrawImperativeAPI>(null)
  useEffect(() => {
    communicator.excalidrawApiRef = ref
  }, [communicator])
  return ref
}

// #endregion hooks
