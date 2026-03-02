package main

import (
	"context" // Import context package
	"database/sql"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"reflect"
	"strings"
	"syscall"
	"time"

	_ "github.com/mattn/go-sqlite3"
	"github.com/mdp/qrterminal"

	"bytes"
	"bufio"
	"io/ioutil"

	"go.mau.fi/whatsmeow"
	waProto "go.mau.fi/whatsmeow/binary/proto"
	"go.mau.fi/whatsmeow/store/sqlstore"
	"go.mau.fi/whatsmeow/types"
	"go.mau.fi/whatsmeow/types/events"
	waLog "go.mau.fi/whatsmeow/util/log"
	"google.golang.org/protobuf/proto"
)

// Declare forwardMap at the package level so it is accessible everywhere
var forwardMap = map[string]string{}

// List of registered numbers that are allowed to get Gemini replies
var registeredNumbers = map[string]bool{}

// Add these new types for the REST API
type RegisteredNumberRequest struct {
	Number string `json:"number"`
}

type RegisteredNumberResponse struct {
	Success bool     `json:"success"`
	Message string   `json:"message"`
	Numbers []string `json:"numbers,omitempty"`
}

// Function to initialize registered numbers from environment variables
func initRegisteredNumbers() {
	// Get registered numbers from environment variable
	registeredNumsStr := os.Getenv("REGISTERED_NUMBERS")
	if registeredNumsStr != "" {
		numbers := strings.Split(registeredNumsStr, ",")
		for _, num := range numbers {
			num = strings.TrimSpace(num)
			if num != "" {
				// Add multiple formats for each number
				registeredNumbers[num+"@s.whatsapp.net"] = true
				registeredNumbers[num] = true
				
				// If it has country code, also add without country code
				if len(num) > 10 && strings.HasPrefix(num, "91") {
					withoutCountry := num[2:]
					registeredNumbers[withoutCountry+"@s.whatsapp.net"] = true
					registeredNumbers[withoutCountry] = true
				}
			}
		}
	}
	
	// Fallback to hardcoded numbers if no environment variable
	if len(registeredNumbers) == 0 {
		registeredNumbers["919515613538@s.whatsapp.net"] = true
		registeredNumbers["9515613538@s.whatsapp.net"] = true
		registeredNumbers["919515613538"] = true
		registeredNumbers["9515613538"] = true
		registeredNumbers["919391547257@s.whatsapp.net"] = true
		registeredNumbers["9391547257@s.whatsapp.net"] = true
		registeredNumbers["919391547257"] = true
		registeredNumbers["9391547257"] = true
	}
	
	fmt.Printf("DEBUG: Loaded %d registered number formats\n", len(registeredNumbers))
}

// Function to check if a JID belongs to a registered number
func isRegisteredNumber(jid string) bool {
	// Debug: Print the JID being checked
	fmt.Printf("DEBUG: Checking if JID '%s' is registered\n", jid)
	
	// Check exact match first
	if registeredNumbers[jid] {
		fmt.Printf("DEBUG: JID '%s' found in registered numbers\n", jid)
		return true
	}
	
	// Extract just the number part (before @) for additional checking
	if strings.Contains(jid, "@") {
		numberPart := strings.Split(jid, "@")[0]
		if registeredNumbers[numberPart] {
			fmt.Printf("DEBUG: Number part '%s' found in registered numbers\n", numberPart)
			return true
		}
	}
	
	fmt.Printf("DEBUG: JID '%s' NOT found in registered numbers\n", jid)
	return false
} 

// Function to add a registered number via API
func addRegisteredNumber(number string) {
	number = strings.TrimSpace(number)
	if number != "" {
		// Add multiple formats for the number
		registeredNumbers[number+"@s.whatsapp.net"] = true
		registeredNumbers[number] = true
		
		// If it has country code, also add without country code
		if len(number) > 10 && strings.HasPrefix(number, "91") {
			withoutCountry := number[2:]
			registeredNumbers[withoutCountry+"@s.whatsapp.net"] = true
			registeredNumbers[withoutCountry] = true
		}
		fmt.Printf("Added registered number: %s (total formats: %d)\n", number, len(registeredNumbers))
	}
}

// Function to remove a registered number via API
func removeRegisteredNumber(number string) {
	number = strings.TrimSpace(number)
	if number != "" {
		// Remove all formats of the number
		delete(registeredNumbers, number+"@s.whatsapp.net")
		delete(registeredNumbers, number)
		
		// If it has country code, also remove without country code
		if len(number) > 10 && strings.HasPrefix(number, "91") {
			withoutCountry := number[2:]
			delete(registeredNumbers, withoutCountry+"@s.whatsapp.net")
			delete(registeredNumbers, withoutCountry)
		}
		fmt.Printf("Removed registered number: %s (remaining formats: %d)\n", number, len(registeredNumbers))
	}
}

// Function to get all registered numbers
func getRegisteredNumbers() []string {
	var numbers []string
	seen := make(map[string]bool)
	
	for jid := range registeredNumbers {
		// Extract just the number part
		number := jid
		if strings.Contains(jid, "@") {
			number = strings.Split(jid, "@")[0]
		}
		
		// Avoid duplicates
		if !seen[number] {
			numbers = append(numbers, number)
			seen[number] = true
		}
	}
	
	return numbers
}

// Handle regular incoming messages with media support
func handleMessage(client *whatsmeow.Client, messageStore *MessageStore, msg *events.Message, logger waLog.Logger) {
	// Save message to database
	chatJID := msg.Info.Chat.String()
	sender := msg.Info.Sender.User

	// Get appropriate chat name (pass nil for conversation since we don't have one for regular messages)
	name := GetChatName(client, messageStore, msg.Info.Chat, chatJID, nil, sender, logger)

	// Update chat in database with the message timestamp (keeps last message time updated)
	err := messageStore.StoreChat(chatJID, name, msg.Info.Timestamp)
	if err != nil {
		logger.Warnf("Failed to store chat: %v", err)
	}

	// Extract text content
	content := extractTextContent(msg.Message)

	// Extract media info
	mediaType, filename, url, mediaKey, fileSHA256, fileEncSHA256, fileLength := extractMediaInfo(msg.Message)

	// Skip if there's no content and no media
	if content == "" && mediaType == "" {
		return
	}

	// Store message in database
	err = messageStore.StoreMessage(
		msg.Info.ID,
		chatJID,
		sender,
		content,
		msg.Info.Timestamp,
		msg.Info.IsFromMe,
		mediaType,
		filename,
		url,
		mediaKey,
		fileSHA256,
		fileEncSHA256,
		fileLength,
	)

	if err != nil {
		logger.Warnf("Failed to store message: %v", err)
	} else {
		timestamp := msg.Info.Timestamp.Format("2006-01-02 15:04:05")
		direction := "←"
		if msg.Info.IsFromMe {
			direction = "→"
		}
		if mediaType != "" {
			fmt.Printf("[%s] %s %s: [%s: %s] %s\n", timestamp, direction, sender, mediaType, filename, content)
		} else if content != "" {
			fmt.Printf("[%s] %s %s: %s\n", timestamp, direction, sender, content)
		}
	}

	// 2. Gemini reply logic
	userMsg := extractTextContent(msg.Message)
	if userMsg == "" {
		return
	}

	if !msg.Info.IsFromMe {
		// Case 1: Someone sent a message TO the QR-scanned number
		// Check if the sender is a registered number
		senderJID := msg.Info.Sender.String()
		fmt.Printf("DEBUG: Received message from senderJID: %s\n", senderJID)
		fmt.Printf("DEBUG: Message content: %s\n", userMsg)
		fmt.Printf("DEBUG: Is from me: %t\n", msg.Info.IsFromMe)
		
		if isRegisteredNumber(senderJID) {
			fmt.Printf("DEBUG: Sender is registered, calling Gemini API\n")
			go func() {
				reply, err := CallGeminiAPI(userMsg)
				if err != nil {
					logger.Warnf("Gemini error: %v", err)
					return
				}
				fmt.Printf("DEBUG: Gemini reply: %s\n", reply)
				success, message := sendWhatsAppMessage(client, msg.Info.Chat.String(), reply, "")
				fmt.Printf("DEBUG: Send result - Success: %t, Message: %s\n", success, message)
			}()
		} else {
			fmt.Printf("DEBUG: Sender is NOT registered, no Gemini reply\n")
		}
	}
	// Case 2: QR-scanned number sent a message TO someone - NO GEMINI REPLY
	// Removed the else block so QR-scanned number doesn't get Gemini replies
} 

func main() {
	// Initialize registered numbers from environment variables
	initRegisteredNumbers()
	
	// Set up logger
	logger := waLog.Stdout("Client", "INFO", true)
	logger.Infof("Starting WhatsApp client...")
} 